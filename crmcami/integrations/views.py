"""Disparador del sync WP desde el SPA (accion, no job async)."""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from . import services


@login_required
@require_POST
def sync_now(request):
    """
    POST {force?: bool} -> corre el sync.
    - Al cargar el SPA: {force:false} (respeta el throttle de 15 min).
    - Boton 'Sincronizar ahora': {force:true} (saltea el throttle).
    Corre SINCRONO dentro del request (compatible con cold start / min-instances=0).
    Fail-open: el servicio nunca rompe la pagina.
    """
    try:
        force = bool(json.loads(request.body or "{}").get("force"))
    except ValueError:
        force = False
    return JsonResponse(services.sync(force=force))
