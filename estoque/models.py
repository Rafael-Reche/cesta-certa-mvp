from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Usuario(AbstractUser):
    """Usuário do sistema (RF01), com perfil e controle de bloqueio (RNF01)."""

    class Perfil(models.TextChoices):
        VOLUNTARIO = "voluntario", "Voluntário"
        COORDENADORA = "coordenadora", "Coordenadora"

    perfil = models.CharField(max_length=20, choices=Perfil.choices, default=Perfil.VOLUNTARIO)
    tentativas_falhas = models.PositiveSmallIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)

    @property
    def e_coordenadora(self):
        return self.perfil == self.Perfil.COORDENADORA

    def esta_bloqueado(self, agora=None):
        agora = agora or timezone.now()
        return self.bloqueado_ate is not None and self.bloqueado_ate > agora

    def bloquear(self, minutos=15, agora=None):
        agora = agora or timezone.now()
        self.bloqueado_ate = agora + timedelta(minutes=minutos)
        self.tentativas_falhas = 0


class Familia(models.Model):
    """Família atendida (RF02). Use somente dados fictícios em demonstrações."""

    codigo = models.CharField("código", max_length=20, unique=True)
    documento = models.CharField("documento", max_length=20, unique=True, null=True, blank=True)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.codigo


class LoteEstoque(models.Model):
    """Lote doado, com validade própria (RF03)."""

    codigo = models.CharField("código", max_length=20, unique=True)
    produto = models.CharField(max_length=80)
    validade = models.DateField()
    doado_kg = models.DecimalField(max_digits=8, decimal_places=2)
    saldo_kg = models.DecimalField(max_digits=8, decimal_places=2)
    priorizado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["validade", "codigo"]
        constraints = [
            models.CheckConstraint(condition=Q(saldo_kg__gte=0), name="lote_saldo_nao_negativo"),
        ]

    def __str__(self):
        return f"{self.codigo} {self.produto}"

    def dias_para_vencer(self, hoje=None):
        hoje = hoje or timezone.localdate()
        return (self.validade - hoje).days


class Entrega(models.Model):
    """Entrega de uma cesta a uma família (RF05)."""

    familia = models.ForeignKey(Familia, on_delete=models.PROTECT, related_name="entregas")
    voluntario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="entregas")
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Entrega {self.pk} - {self.familia}"


class ItemEntrega(models.Model):
    """Quantidade retirada de um lote em uma entrega."""

    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name="itens")
    lote = models.ForeignKey(LoteEstoque, on_delete=models.PROTECT, related_name="itens_entrega")
    quantidade_kg = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantidade_kg__gt=Decimal("0")), name="item_quantidade_positiva"),
        ]

    def __str__(self):
        return f"{self.quantidade_kg} kg de {self.lote}"
