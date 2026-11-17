"""Testes de integração: fluxo completo pelas telas do MVP."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from estoque.models import Entrega, Familia, LoteEstoque, Usuario


def criar_lote(codigo, dias, saldo="12", produto="Tomate"):
    return LoteEstoque.objects.create(
        codigo=codigo,
        produto=produto,
        validade=timezone.localdate() + timedelta(days=dias),
        doado_kg=Decimal(saldo),
        saldo_kg=Decimal(saldo),
    )


class BaseViewTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("voluntario.teste", password="senha-de-teste-123")
        self.familia = Familia.objects.create(codigo="F-0042")
        self.client.force_login(self.usuario)


class AcessoTests(TestCase):
    def test_telas_exigem_login(self):
        for nome in ("painel", "entrega", "alertas", "doacao"):
            resposta = self.client.get(reverse(nome))
            self.assertRedirects(resposta, f"{reverse('entrar')}?next={reverse(nome)}")


class PainelTests(BaseViewTest):
    def test_mostra_as_tres_acoes(self):
        resposta = self.client.get(reverse("painel"))
        for texto in ("Registrar entrega", "Registrar doação", "Ver alertas"):
            self.assertContains(resposta, texto)

    def test_conta_lotes_com_alerta(self):
        criar_lote("H-09", dias=2)
        criar_lote("H-07", dias=5)
        resposta = self.client.get(reverse("painel"))
        self.assertEqual(resposta.context["qtd_alertas"], 1)

    def test_voluntario_nao_ve_cadastro_de_familias(self):
        self.assertNotContains(self.client.get(reverse("painel")), "/admin/")

    def test_coordenadora_ve_cadastro_de_familias(self):
        coordenadora = Usuario.objects.create_user("coord", password="senha-de-teste-123", perfil=Usuario.Perfil.COORDENADORA)
        self.client.force_login(coordenadora)
        self.assertContains(self.client.get(reverse("painel")), "/admin/")


class EntregaTests(BaseViewTest):
    def setUp(self):
        super().setUp()
        self.lote = criar_lote("H-07", dias=5)

    def test_entrega_valida_da_baixa_e_confirma(self):
        resposta = self.client.post(reverse("entrega"), {"familia": "F-0042", "lote": self.lote.pk, "quantidade_kg": "5"}, follow=True)
        self.assertContains(resposta, "Entrega registrada")
        self.lote.refresh_from_db()
        self.assertEqual(self.lote.saldo_kg, Decimal("7"))
        self.assertEqual(Entrega.objects.count(), 1)

    def test_quantidade_acima_do_saldo_mostra_erro_e_nao_altera_o_estoque(self):
        resposta = self.client.post(reverse("entrega"), {"familia": "F-0042", "lote": self.lote.pk, "quantidade_kg": "15"})
        self.assertContains(resposta, "Máximo neste lote: 12 kg")
        self.lote.refresh_from_db()
        self.assertEqual(self.lote.saldo_kg, Decimal("12"))
        self.assertEqual(Entrega.objects.count(), 0)

    def test_familia_inexistente(self):
        resposta = self.client.post(reverse("entrega"), {"familia": "F-9999", "lote": self.lote.pk, "quantidade_kg": "1"})
        self.assertContains(resposta, "Família não encontrada")
        self.assertEqual(Entrega.objects.count(), 0)

    def test_campos_vazios_mostram_erro_junto_aos_campos(self):
        resposta = self.client.post(reverse("entrega"), {})
        self.assertContains(resposta, "Informe a quantidade em kg.")
        self.assertContains(resposta, "Escolha um lote.")

    def test_lote_vencido_nao_e_oferecido(self):
        vencido = criar_lote("H-00", dias=-1)
        resposta = self.client.get(reverse("entrega"))
        self.assertNotIn(vencido, resposta.context["form"].fields["lote"].queryset)

    def test_formulario_tem_rotulos_visiveis(self):
        resposta = self.client.get(reverse("entrega"))
        for rotulo in ("Família (código ou documento)", "Lote a retirar", "Quantidade (kg)", "Confirmar entrega", "Voltar ao painel"):
            self.assertContains(resposta, rotulo)

    def test_tela_mostra_exemplo_do_codigo_da_familia(self):
        resposta = self.client.get(reverse("entrega"))
        self.assertContains(resposta, "Exemplo: F-0042")

    def test_codigo_da_familia_aceita_sem_hifen_e_em_minusculo(self):
        dados = {"familia": "f0042", "lote": self.lote.pk, "quantidade_kg": "2"}
        resposta = self.client.post(reverse("entrega"), dados, follow=True)
        self.assertContains(resposta, "Entrega registrada")
        self.assertEqual(Entrega.objects.count(), 1)

    def test_confirmacao_mostra_resumo_da_entrega(self):
        dados = {"familia": "F-0042", "lote": self.lote.pk, "quantidade_kg": "5"}
        resposta = self.client.post(reverse("entrega"), dados, follow=True)
        self.assertContains(resposta, "Entrega registrada: família F-0042 · lote H-07 Tomate · 5 kg.")


class AlertasTests(BaseViewTest):
    def test_lista_ordenada_com_texto_do_alerta(self):
        criar_lote("H-07", dias=5)
        criar_lote("H-11", dias=3)
        criar_lote("H-09", dias=2)
        resposta = self.client.get(reverse("alertas"))
        codigos = [i["lote"].codigo for i in resposta.context["itens"]]
        self.assertEqual(codigos, ["H-09", "H-11", "H-07"])
        self.assertContains(resposta, "URGENTE · Vence em 2 dias")
        self.assertContains(resposta, "ATENÇÃO · Vence em 3 dias")
        self.assertContains(resposta, "Dentro da validade · 5 dias")
        self.assertContains(resposta, "Resumo do mês")

    def test_priorizar_marca_o_lote(self):
        lote = criar_lote("H-09", dias=2)
        resposta = self.client.post(reverse("priorizar", args=[lote.pk]), follow=True)
        lote.refresh_from_db()
        self.assertTrue(lote.priorizado)
        self.assertContains(resposta, "Priorizado para a próxima cesta")

    def test_priorizar_exige_post(self):
        lote = criar_lote("H-09", dias=2)
        self.assertEqual(self.client.get(reverse("priorizar", args=[lote.pk])).status_code, 405)

    def test_lote_priorizado_aparece_primeiro_na_entrega(self):
        criar_lote("H-07", dias=5)
        urgente = criar_lote("H-11", dias=3)
        outro = criar_lote("H-15", dias=9)
        outro.priorizado = True
        outro.save()
        resposta = self.client.get(reverse("entrega"))
        ordem = [l.codigo for l in resposta.context["form"].fields["lote"].queryset]
        self.assertEqual(ordem[0], "H-15")
        self.assertIn(urgente.codigo, ordem)


class DoacaoTests(BaseViewTest):
    def test_doacao_valida_cria_lote(self):
        validade = (timezone.localdate() + timedelta(days=6)).isoformat()
        resposta = self.client.post(reverse("doacao"), {"codigo": "H-50", "produto": "Cenoura", "validade": validade, "quantidade_kg": "10"}, follow=True)
        self.assertContains(resposta, "Doação registrada")
        self.assertEqual(LoteEstoque.objects.get(codigo="H-50").saldo_kg, Decimal("10"))

    def test_doacao_com_validade_passada_mostra_erro(self):
        validade = (timezone.localdate() - timedelta(days=1)).isoformat()
        resposta = self.client.post(reverse("doacao"), {"codigo": "H-51", "produto": "Cenoura", "validade": validade, "quantidade_kg": "10"})
        self.assertContains(resposta, "A validade não pode estar no passado.")
        self.assertFalse(LoteEstoque.objects.filter(codigo="H-51").exists())
