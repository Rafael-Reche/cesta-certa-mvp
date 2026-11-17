"""Testes unitários das regras de negócio (RF03, RF04, RF05, RF07)."""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from estoque.models import Familia, ItemEntrega, LoteEstoque, Usuario
from estoque.services import (
    NIVEL_ATENCAO,
    NIVEL_OK,
    NIVEL_URGENTE,
    NIVEL_VENCIDO,
    RegraDeNegocioErro,
    descrever_alerta,
    itens_de_alerta,
    nivel_alerta,
    registrar_doacao,
    registrar_entrega,
    resumo_mensal,
)

HOJE = date(2026, 11, 19)


def criar_lote(codigo="H-07", dias=5, saldo="12", produto="Tomate"):
    return LoteEstoque.objects.create(
        codigo=codigo, produto=produto, validade=HOJE + timedelta(days=dias), doado_kg=Decimal(saldo), saldo_kg=Decimal(saldo)
    )


class NivelAlertaTests(TestCase):
    def test_vencido(self):
        self.assertEqual(nivel_alerta(-1), NIVEL_VENCIDO)

    def test_urgente_ate_dois_dias(self):
        self.assertEqual(nivel_alerta(0), NIVEL_URGENTE)
        self.assertEqual(nivel_alerta(2), NIVEL_URGENTE)

    def test_atencao_em_tres_dias(self):
        self.assertEqual(nivel_alerta(3), NIVEL_ATENCAO)

    def test_ok_acima_de_tres_dias(self):
        self.assertEqual(nivel_alerta(4), NIVEL_OK)

    def test_texto_do_alerta_nao_depende_de_cor(self):
        lote = criar_lote(dias=2)
        nivel, texto = descrever_alerta(lote, HOJE)
        self.assertEqual(nivel, NIVEL_URGENTE)
        self.assertEqual(texto, "URGENTE · Vence em 2 dias")
        self.assertEqual(descrever_alerta(criar_lote("H-11", dias=3), HOJE)[1], "ATENÇÃO · Vence em 3 dias")
        self.assertEqual(descrever_alerta(criar_lote("H-12", dias=0), HOJE)[1], "URGENTE · Vence hoje")
        self.assertEqual(descrever_alerta(criar_lote("H-13", dias=-1), HOJE)[1], "VENCIDO")
        self.assertEqual(descrever_alerta(criar_lote("H-14", dias=5), HOJE)[1], "Dentro da validade · 5 dias")


class RegistrarEntregaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("vol", password="senha-de-teste-123")
        self.familia = Familia.objects.create(codigo="F-0042")
        self.lote = criar_lote()

    def test_baixa_reduz_o_saldo_e_cria_item(self):
        entrega = registrar_entrega(usuario=self.usuario, familia=self.familia, lote=self.lote, quantidade_kg="5", hoje=HOJE)
        self.lote.refresh_from_db()
        self.assertEqual(self.lote.saldo_kg, Decimal("7"))
        self.assertEqual(entrega.itens.get().quantidade_kg, Decimal("5"))

    def test_quantidade_acima_do_saldo_e_recusada_sem_alterar_o_estoque(self):
        with self.assertRaises(RegraDeNegocioErro) as ctx:
            registrar_entrega(usuario=self.usuario, familia=self.familia, lote=self.lote, quantidade_kg="15", hoje=HOJE)
        self.assertIn("Máximo neste lote: 12 kg", str(ctx.exception))
        self.lote.refresh_from_db()
        self.assertEqual(self.lote.saldo_kg, Decimal("12"))
        self.assertEqual(ItemEntrega.objects.count(), 0)

    def test_quantidade_zero_ou_negativa_e_recusada(self):
        for valor in ("0", "-3"):
            with self.assertRaises(RegraDeNegocioErro):
                registrar_entrega(usuario=self.usuario, familia=self.familia, lote=self.lote, quantidade_kg=valor, hoje=HOJE)

    def test_quantidade_nao_numerica_e_recusada(self):
        with self.assertRaises(RegraDeNegocioErro):
            registrar_entrega(usuario=self.usuario, familia=self.familia, lote=self.lote, quantidade_kg="abc", hoje=HOJE)

    def test_lote_vencido_e_recusado(self):
        vencido = criar_lote("H-99", dias=-1)
        with self.assertRaises(RegraDeNegocioErro):
            registrar_entrega(usuario=self.usuario, familia=self.familia, lote=vencido, quantidade_kg="1", hoje=HOJE)

    def test_pode_retirar_exatamente_o_saldo(self):
        registrar_entrega(usuario=self.usuario, familia=self.familia, lote=self.lote, quantidade_kg="12", hoje=HOJE)
        self.lote.refresh_from_db()
        self.assertEqual(self.lote.saldo_kg, Decimal("0"))


class RegistrarDoacaoTests(TestCase):
    def test_cria_lote_com_saldo_igual_ao_doado(self):
        lote = registrar_doacao(codigo="H-01", produto="Banana", validade=HOJE + timedelta(days=4), quantidade_kg="8", hoje=HOJE)
        self.assertEqual(lote.saldo_kg, Decimal("8"))
        self.assertEqual(lote.doado_kg, Decimal("8"))

    def test_recusa_validade_no_passado(self):
        with self.assertRaises(RegraDeNegocioErro):
            registrar_doacao(codigo="H-02", produto="Banana", validade=HOJE - timedelta(days=1), quantidade_kg="8", hoje=HOJE)

    def test_recusa_codigo_repetido(self):
        criar_lote("H-03")
        with self.assertRaises(RegraDeNegocioErro):
            registrar_doacao(codigo="H-03", produto="Banana", validade=HOJE + timedelta(days=4), quantidade_kg="8", hoje=HOJE)

    def test_recusa_quantidade_invalida(self):
        with self.assertRaises(RegraDeNegocioErro):
            registrar_doacao(codigo="H-04", produto="Banana", validade=HOJE + timedelta(days=4), quantidade_kg="0", hoje=HOJE)


class ListagemTests(TestCase):
    def test_itens_ordenados_do_vencimento_mais_proximo_ao_mais_distante(self):
        criar_lote("H-07", dias=5)
        criar_lote("H-09", dias=2)
        criar_lote("H-11", dias=3)
        codigos = [i["lote"].codigo for i in itens_de_alerta(HOJE)]
        self.assertEqual(codigos, ["H-09", "H-11", "H-07"])

    def test_lote_sem_saldo_nao_aparece(self):
        lote = criar_lote("H-20")
        lote.saldo_kg = Decimal("0")
        lote.save()
        self.assertEqual(itens_de_alerta(HOJE), [])

    def test_resumo_conta_perdidos_de_lotes_vencidos(self):
        criar_lote("H-30", dias=-2, saldo="4")
        resumo = resumo_mensal(HOJE)
        self.assertEqual(resumo["perdido"], Decimal("4"))
