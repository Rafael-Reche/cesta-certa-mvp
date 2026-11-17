import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.utils import timezone

from .models import Familia, LoteEstoque


class FormularioLogin(AuthenticationForm):
    """RNF01: mensagem genérica, que não revela qual dado está errado."""

    error_messages = {
        "invalid_login": "Usuário ou senha inválidos",
        "inactive": "Usuário ou senha inválidos",
    }


class LoteRadioField(forms.ModelChoiceField):
    def label_from_instance(self, lote):
        from .services import formatar_kg

        return f"{lote.codigo} {lote.produto} · Validade {lote.validade:%d/%m/%Y} · Saldo {formatar_kg(lote.saldo_kg)} kg"


class EntregaForm(forms.Form):
    familia = forms.CharField(
        label="Família (código ou documento)",
        max_length=20,
        widget=forms.TextInput(attrs={"autocomplete": "off", "aria-describedby": "dica-familia"}),
    )
    lote = LoteRadioField(
        label="Lote a retirar",
        queryset=LoteEstoque.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None,
        error_messages={"required": "Escolha um lote.", "invalid_choice": "Escolha um lote disponível."},
    )
    quantidade_kg = forms.DecimalField(
        label="Quantidade (kg)",
        max_digits=8,
        decimal_places=2,
        error_messages={"required": "Informe a quantidade em kg.", "invalid": "Informe um número, por exemplo 5 ou 2,5."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lote"].queryset = LoteEstoque.objects.filter(
            saldo_kg__gt=0, validade__gte=timezone.localdate()
        ).order_by("-priorizado", "validade", "codigo")

    def clean_familia(self):
        valor = self.cleaned_data["familia"].strip()
        # Aceita F0042, f-0042 ou f0042 como F-0042.
        codigo = re.sub(r"^([A-Za-z])-?(\d+)$", lambda m: m.group(1).upper() + "-" + m.group(2), valor)
        familia = Familia.objects.filter(Q(codigo=codigo) | Q(documento=valor), ativa=True).first()
        if familia is None:
            raise forms.ValidationError("Família não encontrada. Confira o código ou o documento.")
        return familia


class DoacaoForm(forms.Form):
    codigo = forms.CharField(label="Código do lote", max_length=20)
    produto = forms.CharField(label="Produto", max_length=80)
    validade = forms.DateField(label="Validade", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    quantidade_kg = forms.DecimalField(label="Quantidade (kg)", max_digits=8, decimal_places=2)
