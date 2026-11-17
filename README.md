# Cesta Certa

Sistema de controle de estoque e entregas para a **Associação Mãos Unidas** (organização fictícia usada na disciplina Projeto de Software, Cruzeiro do Sul).

**Problema:** o controle em cadernos faz perder cerca de 40 kg de hortifrúti por mês por vencimento e consome 2 dias por mês na prestação de contas.
**ODS:** 2 (Fome Zero e Agricultura Sustentável), meta 2.1, com apoio à meta 12.3 do ODS 12.

## Stack
Python 3.12, Django 5.2 (monólito modular em camadas, MVT), SQLite no desenvolvimento, Argon2 para senhas.

## Como rodar
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py makemigrations estoque   # primeira vez: gera as migrações
python manage.py migrate
python manage.py carregar_demo --senha "<escolha uma senha de teste>"
python manage.py runserver
```
Abra http://127.0.0.1:8000/ e entre com `voluntario.teste` (ou `coordenadora.teste`). Todos os dados de demonstração são **fictícios**.

## Testes e cobertura
```bash
python manage.py test
coverage run manage.py test && coverage report
```
O CI (GitHub Actions, `.github/workflows/ci.yml`) roda o build, os testes unitários e de integração e exige 80% de cobertura.

## Estrutura
```
config/            configurações e URLs
estoque/models.py  Usuario, Familia, LoteEstoque, Entrega, ItemEntrega
estoque/services.py regras de negócio (baixa de estoque, alertas, resumo)
estoque/views.py   telas: painel, entrega, doação, alertas
estoque/tests/     testes unitários (services) e de integração (views, login)
```

## Requisitos e situação
| Requisito | Situação |
|---|---|
| RF01 Login com perfis | Implementado (voluntário e coordenadora) |
| RF02 Cadastro de família | Via admin do Django (coordenadora) |
| RF03 Registrar doação | Implementado |
| RF04 Alerta de validade (3 dias) | Implementado |
| RF05 Entrega com baixa | Implementado |
| RF06 Offline com sincronização | **Não implementado** (próxima iteração: Service Worker e IndexedDB) |
| RF07 Relatório mensal | Resumo do mês na tela de alertas |
| RNF01 Segurança de sessão e senha | Argon2, bloqueio após 5 tentativas (15 min), sessão de 2 h |
| RNF04 Acessibilidade | Rótulos, alertas com texto, símbolo e cor, alvos de 44 px (a medir no teste) |

## Fluxo de trabalho e commits
Branch `main` protegida por PR. Trabalho em branches `feat/...`, `fix/...`, `test/...`, `docs/...`, `ci/...`.
Commits semânticos: `feat:`, `fix:`, `test:`, `docs:`, `ci:`, `refactor:`, `chore:`.
Exemplo: `feat: registrar entrega com baixa no saldo do lote`.
Todo PR usa o modelo em `.github/pull_request_template.md` e passa pelo CI antes do merge.

## Segurança
Não registre senhas, chaves ou dados pessoais reais. Em produção defina `DJANGO_ENV=production` e `DJANGO_SECRET_KEY`.
