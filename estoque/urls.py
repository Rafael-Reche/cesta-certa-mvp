from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import FormularioLogin

urlpatterns = [
    path("", views.painel, name="painel"),
    path("entrar/", auth_views.LoginView.as_view(template_name="estoque/entrar.html", authentication_form=FormularioLogin), name="entrar"),
    path("sair/", auth_views.LogoutView.as_view(), name="sair"),
    path("entrega/", views.entrega, name="entrega"),
    path("doacao/", views.doacao, name="doacao"),
    path("alertas/", views.alertas, name="alertas"),
    path("alertas/<int:pk>/priorizar/", views.priorizar, name="priorizar"),
]
