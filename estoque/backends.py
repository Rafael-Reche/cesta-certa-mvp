from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class BackendComBloqueio(ModelBackend):
    """RNF01: usuário bloqueado não autentica, mesmo com a senha correta."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        modelo = get_user_model()
        if username is None:
            username = kwargs.get(modelo.USERNAME_FIELD)
        if username is not None:
            try:
                usuario = modelo._default_manager.get_by_natural_key(username)
            except modelo.DoesNotExist:
                usuario = None
            if usuario is not None and usuario.esta_bloqueado():
                return None
        return super().authenticate(request, username=username, password=password, **kwargs)
