"""
Endpoints JSON del CRM. JsonResponse plano (sin DRF): para 2-3 usuarios y un
puñado de endpoints, DRF seria sobredimensionar.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Lead


def _row(lead):
    """
    Serializa un Lead con las MISMAS claves que el mock ya sabe consumir
    (camelCase: subOrigen/estadoFecha, historial [{ts, text}]). NO mandamos
    'comentarios': el mock lo deriva del historial en normalizeRow().
    """
    return {
        "id": str(lead.id),
        "fecha": lead.fecha.isoformat() if lead.fecha else "",
        "cliente": lead.cliente,
        "servicio": lead.servicio,
        "mail": lead.mail,
        "telefono": lead.telefono,
        "origen": lead.origen,
        "subOrigen": lead.sub_origen,
        "resp": lead.responsable.get_username() if lead.responsable else "",
        "estado": lead.estado,
        "subEstado": lead.sub_estado,
        "estadoFecha": lead.estado_fecha.isoformat() if lead.estado_fecha else "",
        "historial": [
            {"ts": h.ts.isoformat(), "text": h.texto}
            for h in lead.historial.all()
        ],
    }


@login_required
def leads_json(request):
    """GET /api/leads/ -> {leads: [...]}. Detras de login (session auth)."""
    qs = Lead.objects.select_related("responsable").prefetch_related("historial")
    return JsonResponse({"leads": [_row(lead) for lead in qs]})
