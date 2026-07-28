"""
Endpoints JSON del CRM. JsonResponse plano (sin DRF): para 2-3 usuarios y un
puñado de endpoints, DRF seria sobredimensionar.

La logica de negocio (historial, cambio de estado, responsable) vive ACA en el
servidor, no en el cliente: asi es consistente escriba quien escriba (el usuario
o el sync de WordPress).
"""
import json
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from . import normalize
from .models import Lead, LeadHistorial

User = get_user_model()


def _row(lead):
    """Serializa un Lead con las claves que el mock consume (camelCase)."""
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


def _resolve_responsable(resp_name, fallback_user):
    """Nombre del dropdown -> User. Si viene vacio o no existe, el usuario dado."""
    resp_name = (resp_name or "").strip()
    if resp_name:
        u = (
            User.objects.filter(username__iexact=resp_name).first()
            or User.objects.filter(first_name__iexact=resp_name).first()
        )
        if u:
            return u
    return fallback_user


def _apply_fields(lead, data):
    """Vuelca los campos del payload al lead (normalizando lo que corresponde)."""
    lead.cliente = (data.get("cliente") or "").strip()
    lead.fecha = parse_date((data.get("fecha") or "")[:10]) or None
    lead.servicio = normalize.norm_servicio(data.get("servicio"))
    lead.mail = (data.get("mail") or "").strip()[:254]
    lead.telefono = str(data.get("telefono") or "").strip()
    lead.origen = data.get("origen") or ""
    lead.sub_origen = data.get("subOrigen") or ""
    lead.estado = normalize.map_estado(data.get("estado"))
    lead.sub_estado = normalize.norm_sub_estado(lead.estado, data.get("subEstado") or "")


def _hist_estado(lead, prefijo):
    return prefijo + lead.estado + (f" ({lead.sub_estado})" if lead.sub_estado else "")


@login_required
def leads(request):
    """GET -> lista de leads. POST -> crea un lead."""
    if request.method == "POST":
        data = json.loads(request.body or "{}")
        if not (data.get("cliente") or "").strip():
            return JsonResponse({"ok": False, "error": "cliente requerido"}, status=400)
        with transaction.atomic():
            lead = Lead()
            _apply_fields(lead, data)
            lead.responsable = _resolve_responsable(data.get("resp"), request.user)
            lead.estado_fecha = lead.fecha or date.today()
            lead.save()
            now = timezone.now()
            LeadHistorial.objects.create(
                lead=lead, ts=now, autor=request.user,
                texto=_hist_estado(lead, "Alta del lead · Estado: "),
            )
            nc = (data.get("nuevoComentario") or "").strip()
            if nc:
                LeadHistorial.objects.create(lead=lead, ts=now, autor=request.user, texto=nc)
        return JsonResponse({"ok": True, "lead": _row(lead)}, status=201)

    qs = Lead.objects.select_related("responsable").prefetch_related("historial")
    return JsonResponse({"leads": [_row(lead) for lead in qs]})


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def lead_detail(request, pk):
    """POST -> edita el lead. El server maneja el historial y estado_fecha."""
    lead = get_object_or_404(Lead, pk=pk)
    data = json.loads(request.body or "{}")
    prev = (lead.estado, lead.sub_estado)

    _apply_fields(lead, data)
    if (data.get("resp") or "").strip():
        lead.responsable = _resolve_responsable(
            data.get("resp"), lead.responsable or request.user
        )

    now = timezone.now()
    estado_cambio = prev != (lead.estado, lead.sub_estado)
    if estado_cambio:
        lead.estado_fecha = date.today()
    lead.save()

    if estado_cambio:
        LeadHistorial.objects.create(
            lead=lead, ts=now, autor=request.user,
            texto=_hist_estado(lead, "Cambio de estado a "),
        )
    nc = (data.get("nuevoComentario") or "").strip()
    if nc:
        LeadHistorial.objects.create(lead=lead, ts=now, autor=request.user, texto=nc)

    return JsonResponse({"ok": True, "lead": _row(lead)})
