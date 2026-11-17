"""Configurações do Cesta Certa (MVP)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCAO = os.environ.get("DJANGO_ENV") == "production"
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-inseguro-trocar-em-producao")
if PRODUCAO and SECRET_KEY.startswith("dev-inseguro"):
    raise RuntimeError("Defina DJANGO_SECRET_KEY em produção.")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "estoque.apps.EstoqueConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Banco local (SQLite). Para PostgreSQL gerenciado, trocar este bloco e
# instalar psycopg (decisão da arquitetura; fora desta primeira versão).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "estoque.Usuario"

# RNF01: Argon2 como hash principal de senha.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTHENTICATION_BACKENDS = ["estoque.backends.BackendComBloqueio"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "entrar"
LOGIN_REDIRECT_URL = "painel"
LOGOUT_REDIRECT_URL = "entrar"

# RNF01: sessão expira após 2 h sem atividade; cookies protegidos.
SESSION_COOKIE_AGE = 2 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = PRODUCAO
CSRF_COOKIE_SECURE = PRODUCAO
SECURE_SSL_REDIRECT = PRODUCAO

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
