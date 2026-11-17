"""Verificação de saúde: usada pelo Render e pelo monitoramento externo."""
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def saude(request):
    """Responde 200 se a aplicação e o banco estão de pé; 503 caso contrário."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "erro", "banco": "indisponivel"}, status=503)
    return JsonResponse({"status": "ok", "banco": "ok"})
