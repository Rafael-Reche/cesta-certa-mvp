from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import DoacaoForm, EntregaForm
from .models import LoteEstoque
from .services import (
    NIVEL_OK,
    RegraDeNegocioErro,
    formatar_kg,
    itens_de_alerta,
    registrar_doacao,
    registrar_entrega,
    resumo_mensal,
)


@login_required
def painel(request):
    """Tela 1: menu inicial com as três ações do dia."""
    qtd_alertas = sum(1 for item in itens_de_alerta() if item["nivel"] != NIVEL_OK)
    return render(request, "estoque/painel.html", {"qtd_alertas": qtd_alertas})


@login_required
def entrega(request):
    """Tela 2: registrar entrega (RF05)."""
    form = EntregaForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            registrar_entrega(
                usuario=request.user,
                familia=form.cleaned_data["familia"],
                lote=form.cleaned_data["lote"],
                quantidade_kg=form.cleaned_data["quantidade_kg"],
            )
        except RegraDeNegocioErro as erro:
            form.add_error("quantidade_kg", str(erro))
        else:
            dados = form.cleaned_data
            messages.success(
                request,
                f"Entrega registrada: família {dados['familia'].codigo} · lote {dados['lote'].codigo} {dados['lote'].produto} · {formatar_kg(dados['quantidade_kg'])} kg.",
            )
            return redirect("entrega")
    return render(request, "estoque/entrega.html", {"form": form})


@login_required
def alertas(request):
    """Tela 3: alertas de validade e resumo do mês (RF04, RF07)."""
    contexto = {"itens": itens_de_alerta(), "resumo": resumo_mensal(), "nivel_ok": NIVEL_OK}
    return render(request, "estoque/alertas.html", contexto)


@login_required
@require_POST
def priorizar(request, pk):
    lote = get_object_or_404(LoteEstoque, pk=pk)
    lote.priorizado = True
    lote.save(update_fields=["priorizado"])
    messages.success(request, f"{lote.codigo} priorizado para a próxima cesta.")
    return redirect("alertas")


@login_required
def doacao(request):
    """Registrar doação (RF03)."""
    form = DoacaoForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            lote = registrar_doacao(**form.cleaned_data)
        except RegraDeNegocioErro as erro:
            form.add_error(None, str(erro))
        else:
            messages.success(request, f"Doação registrada no lote {lote.codigo}.")
            return redirect("doacao")
    return render(request, "estoque/doacao.html", {"form": form})
