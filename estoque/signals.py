from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

LIMITE_TENTATIVAS = 5
MINUTOS_BLOQUEIO = 15


@receiver(user_login_failed)
def registrar_falha_de_login(sender, credentials, request=None, **kwargs):
    username = credentials.get("username")
    if not username:
        return
    modelo = get_user_model()
    try:
        usuario = modelo._default_manager.get_by_natural_key(username)
    except modelo.DoesNotExist:
        return
    if usuario.esta_bloqueado():
        return
    usuario.tentativas_falhas += 1
    if usuario.tentativas_falhas >= LIMITE_TENTATIVAS:
        usuario.bloquear(MINUTOS_BLOQUEIO)
    usuario.save(update_fields=["tentativas_falhas", "bloqueado_ate"])


@receiver(user_logged_in)
def zerar_falhas_no_login(sender, user, request=None, **kwargs):
    if getattr(user, "tentativas_falhas", 0) or getattr(user, "bloqueado_ate", None):
        user.tentativas_falhas = 0
        user.bloqueado_ate = None
        user.save(update_fields=["tentativas_falhas", "bloqueado_ate"])
