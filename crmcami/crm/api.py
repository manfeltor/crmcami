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
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_http_methods

from . import choices, normalize
from .models import Lead, LeadHistorial, TallyNoComercial

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


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def bulk_estado(request):
    """POST {ids, estado} -> cambia el estado de los leads seleccionados."""
    data = json.loads(request.body or "{}")
    ids = data.get("ids") or []
    nuevo = (data.get("estado") or "").strip()
    if nuevo not in choices.ESTADOS:
        return JsonResponse({"ok": False, "error": "estado invalido"}, status=400)

    now = timezone.now()
    afectados = 0
    for lead in Lead.objects.filter(id__in=ids):
        if lead.estado != nuevo:
            LeadHistorial.objects.create(
                lead=lead, ts=now, autor=request.user,
                texto="Cambio de estado a " + nuevo,
            )
        lead.estado = nuevo
        lead.sub_estado = ""
        lead.estado_fecha = date.today()
        lead.save()
        afectados += 1
    return JsonResponse({"ok": True, "afectados": afectados})


@login_required
@require_http_methods(["POST"])
def bulk_delete(request):
    """POST {ids} -> elimina los leads seleccionados (borra su historial en cascada)."""
    data = json.loads(request.body or "{}")
    ids = data.get("ids") or []
    qs = Lead.objects.filter(id__in=ids)
    count = qs.count()
    qs.delete()
    return JsonResponse({"ok": True, "eliminados": count})


@login_required
def tally(request):
    """
    GET  -> {tally: {fecha: {categoria: cantidad}}} (lo que consume el mock).
    POST {fecha, categoria, delta} -> suma/resta al contador (nunca baja de 0).
    """
    if request.method == "POST":
        data = json.loads(request.body or "{}")
        fecha = parse_date((data.get("fecha") or "")[:10])
        cat = (data.get("categoria") or "").strip()
        try:
            delta = int(data.get("delta") or 0)
        except (TypeError, ValueError):
            delta = 0
        if not fecha or cat not in choices.NOCOM_CATS:
            return JsonResponse({"ok": False, "error": "datos invalidos"}, status=400)
        obj, _ = TallyNoComercial.objects.get_or_create(
            fecha=fecha, categoria=cat, defaults={"cantidad": 0}
        )
        obj.cantidad = max(0, obj.cantidad + delta)
        obj.save()
        return JsonResponse({"ok": True, "cantidad": obj.cantidad})

    out = {}
    for t in TallyNoComercial.objects.all():
        out.setdefault(t.fecha.isoformat(), {})[t.categoria] = t.cantidad
    return JsonResponse({"tally": out})


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def leads_import(request):
    """
    POST {rows: [...]} -> REEMPLAZA todos los leads por los importados.
    Destructivo (como el mock). El parseo del Excel se hace en el cliente; aca
    normalizamos y persistimos. Cada row viene con las claves del mock.
    """
    data = json.loads(request.body or "{}")
    rows = data.get("rows") or []

    LeadHistorial.objects.all().delete()
    Lead.objects.all().delete()

    creados = 0
    for r in rows:
        cliente = (r.get("cliente") or "").strip()
        if not cliente:
            continue
        estado = normalize.map_estado(r.get("estado"))
        lead = Lead.objects.create(
            fecha=parse_date((r.get("fecha") or "")[:10]) or None,
            cliente=cliente,
            servicio=normalize.norm_servicio(r.get("servicio")),
            mail=(r.get("mail") or "").strip()[:254],
            telefono=str(r.get("telefono") or "").strip(),
            origen=r.get("origen") or "",
            sub_origen=r.get("subOrigen") or "",
            responsable=_resolve_responsable(r.get("resp"), None),
            estado=estado,
            sub_estado=normalize.norm_sub_estado(estado, r.get("subEstado") or ""),
            estado_fecha=parse_date((r.get("estadoFecha") or "")[:10]) or None,
        )
        for h in (r.get("historial") or []):
            ts = parse_datetime(h.get("ts") or "") or timezone.now()
            if timezone.is_naive(ts):
                ts = timezone.make_aware(ts)
            LeadHistorial.objects.create(lead=lead, ts=ts, texto=h.get("text") or "")
        creados += 1

    return JsonResponse({"ok": True, "importados": creados})
