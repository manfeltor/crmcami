"""
Constantes de negocio portadas del mock (crm_mock.html).
Se usan como `choices` en los modelos. Para 2-3 usuarios no vale la pena
hacerlas editables por UI (tablas de config); si escala, se mueven despues.
"""

# --- Servicios -------------------------------------------------------------
SERVICIO_ALMACENAMIENTO = "Almacenamiento"
SERVICIO_CROSSDOCKING = "Cross-docking"
SERVICIOS = [SERVICIO_ALMACENAMIENTO, SERVICIO_CROSSDOCKING]
SERVICIO_CHOICES = [(s, s) for s in SERVICIOS]

# --- Origenes --------------------------------------------------------------
ORIGENES = [
    "Google Ads",
    "Meta Ads",
    "Redes sociales",
    "Referido",
    "Sitio web",
    "SIGNOS",
]
ORIGEN_CHOICES = [(o, o) for o in ORIGENES]

# --- Estados ---------------------------------------------------------------
ESTADO_DATOS_PENDIENTES = "1. Datos pendientes"
ESTADO_PENDIENTE_COTIZAR = "2. Pendiente cotizar"
ESTADO_COTIZADO = "3. Cotizado"
ESTADO_INTERESADO = "4. Interesado"
ESTADO_NEGOCIANDO = "5. Negociando / Re-cotizar"
ESTADO_GANADA = "6. Venta ganada"
ESTADO_NO_VIABLE = "7. No viable"
ESTADO_NO_AVANZO = "8. No avanzó"

ESTADOS = [
    ESTADO_DATOS_PENDIENTES,
    ESTADO_PENDIENTE_COTIZAR,
    ESTADO_COTIZADO,
    ESTADO_INTERESADO,
    ESTADO_NEGOCIANDO,
    ESTADO_GANADA,
    ESTADO_NO_VIABLE,
    ESTADO_NO_AVANZO,
]
ESTADO_CHOICES = [(e, e) for e in ESTADOS]

# estados terminales / abiertos (para KPIs y la logica de alertas)
ESTADOS_FINALES = [ESTADO_GANADA, ESTADO_NO_VIABLE, ESTADO_NO_AVANZO]
ESTADOS_ABIERTOS = [
    ESTADO_DATOS_PENDIENTES,
    ESTADO_PENDIENTE_COTIZAR,
    ESTADO_COTIZADO,
    ESTADO_INTERESADO,
    ESTADO_NEGOCIANDO,
]

# color por estado (para los graficos / badges del front)
ESTADO_COLOR = {
    ESTADO_DATOS_PENDIENTES: "#6b7280",
    ESTADO_PENDIENTE_COTIZAR: "#d97706",
    ESTADO_COTIZADO: "#2563eb",
    ESTADO_INTERESADO: "#7c3aed",
    ESTADO_NEGOCIANDO: "#0891b2",
    ESTADO_GANADA: "#059669",
    ESTADO_NO_VIABLE: "#dc2626",
    ESTADO_NO_AVANZO: "#9ca3af",
}

# --- Sub-estados (solo aplican a los estados 7 y 8) ------------------------
SUB_NOAVANZO = [
    "Sin respuesta",
    "Eligió competencia",
    "Cotización fuera de presupuesto",
    "Proyecto pospuesto",
    "Tardanza comercial",
    "Otro",
]
SUB_NOVIABLE = [
    "SENASA",
    "ANMAT",
    "RENPRE",
    "Transporte",
    "Fuera de alcance geográfico",
    "Otro",
]
# union sin duplicados ("Otro" esta en ambas listas)
SUB_ESTADO_CHOICES = [(s, s) for s in dict.fromkeys(SUB_NOAVANZO + SUB_NOVIABLE)]


def sub_estados_para(estado):
    """Sub-estados validos segun el estado (para validar/filtrar en el form)."""
    if estado == ESTADO_NO_VIABLE:
        return SUB_NOVIABLE
    if estado == ESTADO_NO_AVANZO:
        return SUB_NOAVANZO
    return []


# --- Leads no comerciales --------------------------------------------------
NOCOM_CATS = ["Empleo / RRHH", "Proveedores", "Otro / Spam"]
NOCOM_CHOICES = [(c, c) for c in NOCOM_CATS]

# umbral de la alerta "+N dias sin avances"
DIAS_ALERTA_STALE = 30
