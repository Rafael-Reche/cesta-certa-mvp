"""Testes da rota de saúde e da configuração de produção."""
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class SaudeTests(TestCase):
    def test_saude_publica_responde_ok(self):
        resposta = self.client.get(reverse("saude"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"status": "ok", "banco": "ok"})

    def test_saude_responde_503_se_banco_falhar(self):
        with mock.patch("estoque.saude.connection.cursor", side_effect=Exception("banco fora")):
            resposta = self.client.get(reverse("saude"))
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.json()["status"], "erro")

    def test_saude_nao_aceita_post(self):
        self.assertEqual(self.client.post(reverse("saude")).status_code, 405)

    def test_saude_nao_expoe_dados_internos(self):
        corpo = self.client.get(reverse("saude")).content.decode()
        self.assertNotIn("SECRET", corpo)
        self.assertNotIn("sqlite", corpo.lower())

    def test_admin_usa_endereco_configurado(self):
        resposta = self.client.get("/" + settings.ADMIN_URL, follow=False)
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("login", resposta["Location"])
