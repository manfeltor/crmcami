"""
Orquestacion del sync WordPress -> CRM (pull).

- Marca de agua (watermark) forward-only: solo procesa submissions con id >
  watermark y avanza la marca. Un lead borrado NO reaparece (su id ya quedo
  atras de la marca).
- Corte por fecha: solo importa submissions con created_at >= WP_SYNC_CUTOFF
  (para no traer los ~1600 historicos en el primer sync).
- Dedup por Lead.wp_entry_id (unique) como red secundaria.
- Fail-open: si WP no responde, se loguea y se reintenta luego.
- Append-only: las submissions son inmutables.
"""
import logging
from datetime import date, timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from crm.models import Lead, LeadHistorial

from .models import SyncState
from .wordpress import client, mapper

logger = logging.getLogger(__name__)


def debe_sincronizar(state=None):
    """True si nunca se sincronizo o si paso el tiempo del throttle."""
    state = state or SyncState.solo()
    if state.last_sync_at is None:
        return True
    limite = timedelta(minutes=settings.WP_SYNC_THROTTLE_MINUTES)
    return timezone.now() - state.last_sync_at >= limite


def sync(force=False, dry_run=False):
    """
    Ejecuta el pull. `force` saltea el throttle (boton 'Sincronizar ahora').
    `dry_run` cuenta pero no escribe ni avanza la marca.
    """
    state = SyncState.solo()
    if not force and not dry_run and not debe_sincronizar(state):
        return {"skipped": True, "reason": "throttled", "importados": 0}

    cutoff = parse_date(settings.WP_SYNC_CUTOFF) or date(2026, 1, 1)
    watermark = state.watermark
    max_id = watermark
    importados = 0
    considerados = 0
    fallidos = 0
    errores = []

    for form_id in mapper.FORM_IDS:
        try:
            entries = client.fetch_form(form_id)
        except client.WordPressUnavailable as e:
            errores.append(f"form {form_id}: {e}")
            continue

        for entry in entries:
            try:
                eid = int(entry.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if eid <= watermark:
                continue
            if eid > max_id:
                max_id = eid  # avanza la marca aunque despues no se importe

            lead_kwargs, comentario, created = mapper.entry_to_lead(form_id, entry)

            # corte por fecha
            if created and created.date() < cutoff:
                continue
            # sin datos utiles
            if not lead_kwargs["cliente"] and not lead_kwargs["mail"]:
                continue

            considerados += 1
            if dry_run:
                importados += 1
                continue

            try:
                with transaction.atomic():
                    lead = Lead.objects.create(**lead_kwargs)
                    ts = created or timezone.now()
                    if timezone.is_naive(ts):
                        ts = timezone.make_aware(ts)
                    LeadHistorial.objects.create(
                        lead=lead, ts=ts,
                        texto=comentario or "Alta automatica desde el sitio web (WordPress).",
                    )
                    importados += 1
            except IntegrityError:
                continue  # wp_entry_id duplicado -> ya estaba
            except Exception as e:  # noqa: BLE001  fila con datos raros: saltear, no frenar
                logger.warning("Sync: entry %s fallo: %s", lead_kwargs.get("wp_entry_id"), e)
                fallidos += 1
                continue

    if not dry_run:
        state.watermark = max_id
        state.last_sync_at = timezone.now()
        state.last_ok = not errores
        state.last_error = "; ".join(errores)
        state.last_importados = importados
        state.save()

    logger.info("Sync WP: importados=%s considerados=%s wm=%s", importados, considerados, max_id)
    return {
        "skipped": False, "ok": not errores, "importados": importados,
        "considerados": considerados, "fallidos": fallidos,
        "watermark_nuevo": max_id, "errores": errores, "dry_run": dry_run,
    }
