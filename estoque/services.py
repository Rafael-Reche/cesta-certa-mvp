"""Regras de negócio do estoque, separadas das views para facilitar os testes."""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Entrega, ItemEntrega, LoteEstoque

NIVEL_VENCIDO = "vencido"
NIVEL_URGENTE = "urgente"
NIVEL_ATENCAO = "atencao"
NIVEL_OK = "ok"

DIAS_URGENTE = 2
DIAS_ALERTA = 3  # RF04: alerta quando faltam 3 dias ou menos


class RegraDeNegocioErro(ValueError):
    """Violação de uma regra de negócio, com mensagem pronta para o usuário."""


def nivel_alerta(dias):
    if dias < 0:
        return NIVEL_VENCIDO
    if dias <= DIAS_URGENTE:
        return NIVEL_URGENTE
    if dias <= DIAS_ALERTA:
        return NIVEL_ATENCAO
    return NIVEL_OK


def descrever_alerta(lote, hoje=None):
    """Retorna (nível, texto) do alerta de um lote; o texto não depende de cor."""
    dias = lote.dias_para_vencer(hoje)
    nivel = nivel_alerta(dias)
    if nivel == NIVEL_VENCIDO:
        return nivel, "VENCIDO"
    if nivel == NIVEL_URGENTE:
        quando = "Vence hoje" if dias == 0 else f"Vence em {dias} dia{'s' if dias != 1 else ''}"
        return nivel, f"URGENTE · {quando}"
    if nivel == NIVEL_ATENCAO:
        return nivel, f"ATENÇÃO · Vence em {dias} dias"
    return nivel, f"Dentro da validade · {dias} dias"


def formatar_kg(valor):
    return format(Decimal(valor).normalize(), "f")


def _como_decimal(valor):
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise RegraDeNegocioErro("Informe uma quantidade válida.")


@transaction.atomic
def registrar_entrega(*, usuario, familia, lote, quantidade_kg, hoje=None):
    """RF05: registra a entrega e dá baixa no saldo do lote."""
    hoje = hoje or timezone.localdate()
    quantidade = _como_decimal(quantidade_kg)
    if quantidade <= 0:
        raise RegraDeNegocioErro("Informe uma quantidade maior que zero.")
    lote = LoteEstoque.objects.select_for_update().get(pk=lote.pk)
    if lote.validade < hoje:
        raise RegraDeNegocioErro("Este lote está vencido e não pode ser entregue.")
    if quantidade > lote.saldo_kg:
        raise RegraDeNegocioErro(f"Máximo neste lote: {formatar_kg(lote.saldo_kg)} kg. Corrija a quantidade.")
    entrega = Entrega.objects.create(familia=familia, voluntario=usuario)
    ItemEntrega.objects.create(entrega=entrega, lote=lote, quantidade_kg=quantidade)
    lote.saldo_kg -= quantidade
    lote.save(update_fields=["saldo_kg"])
    return entrega


@transaction.atomic
def registrar_doacao(*, codigo, produto, validade, quantidade_kg, hoje=None):
    """RF03: cria um lote com validade própria."""
    hoje = hoje or timezone.localdate()
    quantidade = _como_decimal(quantidade_kg)
    if quantidade <= 0:
        raise RegraDeNegocioErro("Informe uma quantidade maior que zero.")
    if validade < hoje:
        raise RegraDeNegocioErro("A validade não pode estar no passado.")
    if LoteEstoque.objects.filter(codigo=codigo).exists():
        raise RegraDeNegocioErro("Já existe um lote com este código.")
    return LoteEstoque.objects.create(codigo=codigo, produto=produto, validade=validade, doado_kg=quantidade, saldo_kg=quantidade)


def lotes_ativos():
    return LoteEstoque.objects.filter(saldo_kg__gt=0).order_by("validade", "codigo")


def itens_de_alerta(hoje=None):
    """Lotes com saldo, do vencimento mais próximo ao mais distante (RF04)."""
    hoje = hoje or timezone.localdate()
    itens = []
    for lote in lotes_ativos():
        nivel, texto = descrever_alerta(lote, hoje)
        itens.append({"lote": lote, "nivel": nivel, "texto": texto, "dias": lote.dias_para_vencer(hoje)})
    return itens


def resumo_mensal(hoje=None):
    """RF07 (desejável): doado, entregue e perdido no mês corrente."""
    hoje = hoje or timezone.localdate()
    inicio = hoje.replace(day=1)
    zero = Decimal("0")
    doado = LoteEstoque.objects.filter(criado_em__date__gte=inicio).aggregate(t=Sum("doado_kg"))["t"] or zero
    entregue = ItemEntrega.objects.filter(entrega__criada_em__date__gte=inicio).aggregate(t=Sum("quantidade_kg"))["t"] or zero
    perdido = LoteEstoque.objects.filter(validade__lt=hoje).aggregate(t=Sum("saldo_kg"))["t"] or zero
    return {"doado": doado, "entregue": entregue, "perdido": perdido}
