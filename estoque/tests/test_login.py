"""Testes de autenticação e bloqueio (RF01, RNF01)."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from estoque.models import Usuario

SENHA = "senha-de-teste-123"


class LoginTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("voluntario.teste", password=SENHA)

    def entrar(self, senha):
        return self.client.post(reverse("entrar"), {"username": "voluntario.teste", "password": senha})

    def autenticado(self):
        return "_auth_user_id" in self.client.session

    def test_login_valido_vai_para_o_painel(self):
        self.assertRedirects(self.entrar(SENHA), reverse("painel"))

    def test_erro_generico_nao_revela_qual_dado_falhou(self):
        resposta = self.entrar("errada")
        self.assertContains(resposta, "Usuário ou senha inválidos")
        resposta = self.client.post(reverse("entrar"), {"username": "inexistente", "password": "x"})
        self.assertContains(resposta, "Usuário ou senha inválidos")

    def test_senha_guardada_com_argon2(self):
        self.assertTrue(self.usuario.password.startswith("argon2"))

    def test_bloqueia_apos_cinco_tentativas_mesmo_com_senha_correta(self):
        for _ in range(5):
            self.entrar("errada")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.esta_bloqueado())
        resposta = self.entrar(SENHA)
        self.assertContains(resposta, "Usuário ou senha inválidos")
        self.assertFalse(self.autenticado())

    def test_bloqueio_expira_depois_de_15_minutos(self):
        self.usuario.bloqueado_ate = timezone.now() - timedelta(minutes=1)
        self.usuario.save()
        self.assertRedirects(self.entrar(SENHA), reverse("painel"))

    def test_login_com_sucesso_zera_as_tentativas(self):
        self.entrar("errada")
        self.entrar(SENHA)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.tentativas_falhas, 0)

    def test_logout_exige_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse("sair")).status_code, 405)
        self.client.post(reverse("sair"))
        self.assertFalse(self.autenticado())
