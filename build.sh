#!/usr/bin/env bash
# Build no Render: instala dependências e reúne os arquivos estáticos.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
