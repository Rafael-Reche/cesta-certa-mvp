#!/usr/bin/env bash
# Início no Render: migra o banco, carrega os dados FICTÍCIOS de demonstração
# (apenas se DEMO_SENHA estiver definida) e sobe o servidor.
set -o errexit
python manage.py migrate --noinput
if [ -n "$DEMO_SENHA" ]; then
  python manage.py carregar_demo --senha "$DEMO_SENHA"
fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 60
