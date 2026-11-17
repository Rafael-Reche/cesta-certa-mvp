"""Carrega dados FICTÍCIOS para demonstração e teste de usabilidade."""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from estoque.models import Familia, LoteEstoque, Usuario


class Command(BaseCommand):
    help = "Cria usuários, uma família e três lotes fictícios (use --senha para definir a senha de teste)."

    def add_arguments(self, parser):
        parser.add_argument("--senha", required=True, help="Senha de teste para os usuários fictícios.")

    def handle(self, *args, **opcoes):
        hoje = timezone.localdate()
        for username, perfil, staff in (("voluntario.teste", "voluntario", False), ("coordenadora.teste", "coordenadora", True)):
            usuario, _ = Usuario.objects.get_or_create(username=username, defaults={"perfil": perfil, "is_staff": staff})
            usuario.set_password(opcoes["senha"])
            usuario.save()
        Familia.objects.get_or_create(codigo="F-0042")
        lotes = (
            ("H-07", "Tomate", 5, "12"),
            ("H-09", "Banana prata", 2, "8"),
            ("H-11", "Alface crespa", 3, "6"),
        )
        for codigo, produto, dias, kg in lotes:
            LoteEstoque.objects.get_or_create(
                codigo=codigo,
                defaults={"produto": produto, "validade": hoje + timedelta(days=dias), "doado_kg": Decimal(kg), "saldo_kg": Decimal(kg)},
            )
        self.stdout.write(self.style.SUCCESS("Dados fictícios carregados."))
