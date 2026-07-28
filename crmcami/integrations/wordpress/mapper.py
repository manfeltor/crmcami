"""
Mapeo entry de Formidable -> campos de Lead. Una config por form (los nombres
de campo difieren entre forms — ver scripts/wp_discovery.py).

Descubierto el 2026-07-28 contra los forms 3/4/5 activos:
  - Form 3 (principal website): el servicio viene del campo "Me interesa el servicio".
  - Form 4 (Landing Crossdock): servicio fijo = Cross-docking.
  - Form 5 (Landing Fulfillment): servicio fijo = Almacenamiento.
"""
from django.utils.dateparse import parse_datetime

from crm import choices, normalize

FORM_CONFIG = {
    3: {
        "nombre": "Formulario principal del website",
        "servicio_fijo": None,
        "servicio_field": "Me interesa el servicio",
        "cliente": "Razón social",
        "mail": "E-mail",
        "telefono": "Telefono",
        "mensaje": "Mensaje",
        "contacto": None,
        "extras": [],
    },
    4: {
        "nombre": "Landing Crossdock",
        "servicio_fijo": choices.SERVICIO_CROSSDOCKING,
        "servicio_field": None,
        "cliente": "Razón Social o nombre de la empresa",
        "mail": "Correo electrónico",
        "telefono": "Teléfono",
        "mensaje": "Completa tu mensaje",
        "contacto": "Nombre y Apellido",
        "extras": ["Cantidad de pedidos mensuales"],
    },
    5: {
        "nombre": "Landing Fulfillment",
        "servicio_fijo": choices.SERVICIO_ALMACENAMIENTO,
        "servicio_field": None,
        "cliente": "Razón Social o nombre de la empresa",
        "mail": "Correo electrónico empresarial",
        "telefono": "Teléfono",
        "mensaje": "Contanos sobre tu proyecto",
        "contacto": "Nombre y Apellido",
        "extras": [],
    },
}

FORM_IDS = list(FORM_CONFIG.keys())


def entry_to_lead(form_id, entry):
    """
    Devuelve (lead_kwargs, comentario, created_dt).
    `created_dt` es datetime (naive) o None; el caller lo usa para el corte y el
    ts del historial.
    """
    cfg = FORM_CONFIG[form_id]

    def g(key):
        return str(entry.get(key, "")).strip() if key else ""

    servicio = cfg["servicio_fijo"] or normalize.norm_servicio(g(cfg["servicio_field"]))
    if servicio not in choices.SERVICIOS:
        servicio = ""  # valor no reconocido -> blanco (servicio es choices, no texto libre)

    # comentario inicial: contacto + mensaje + extras (lo que no entra en columnas)
    partes = []
    if cfg["contacto"] and g(cfg["contacto"]):
        partes.append("Contacto: " + g(cfg["contacto"]))
    if g(cfg["mensaje"]):
        partes.append("Mensaje: " + g(cfg["mensaje"]))
    for ex in cfg["extras"]:
        if g(ex):
            partes.append(ex + ": " + g(ex))
    comentario = " · ".join(partes)

    created = parse_datetime(g("created_at"))

    lead_kwargs = {
        "wp_entry_id": str(entry.get("id") or "").strip(),
        "cliente": g(cfg["cliente"])[:255],
        "mail": g(cfg["mail"])[:254],
        "telefono": g(cfg["telefono"])[:50],
        "servicio": servicio,
        "origen": "Sitio web",
        "sub_origen": cfg["nombre"],
        "estado": choices.ESTADO_DATOS_PENDIENTES,
        "fecha": created.date() if created else None,
        "estado_fecha": created.date() if created else None,
    }
    return lead_kwargs, comentario, created
