"""
Normalizacion de datos sucios — PORTADA del JS del mock (mapEstado /
normServicio / mapResp).

FUENTE UNICA: la van a reusar el import de la data legacy y el sync de
WordPress (Formidable manda campos con texto libre / inconsistente). NUNCA
guardar strings crudos: la data original trae numeracion vieja de estados,
servicios mal escritos ("Croosdock") y responsables inconsistentes ("Cami R").
"""
from . import choices


def norm_servicio(s):
    if not s:
        return ""
    t = str(s).lower()
    if "cross" in t or "croos" in t:
        return choices.SERVICIO_CROSSDOCKING
    if "almac" in t or "fulfil" in t:
        return choices.SERVICIO_ALMACENAMIENTO
    return s


def map_estado(raw):
    t = str(raw or "").lower()
    if "ganada" in t:
        return choices.ESTADO_GANADA
    if "no viable" in t:
        return choices.ESTADO_NO_VIABLE
    if "no avanz" in t or "sin respuesta" in t:
        return choices.ESTADO_NO_AVANZO
    if "negoci" in t or "re-cotiz" in t or "recotiz" in t:
        return choices.ESTADO_NEGOCIANDO
    if "interesad" in t:
        return choices.ESTADO_INTERESADO
    if "cotizado" in t:
        return choices.ESTADO_COTIZADO
    if "pend" in t and "cotiz" in t:
        return choices.ESTADO_PENDIENTE_COTIZAR
    if "dato" in t or "pend" in t:
        return choices.ESTADO_DATOS_PENDIENTES
    return choices.ESTADO_DATOS_PENDIENTES


def map_responsable_nombre(raw):
    """
    Devuelve el nombre canonico ("Camila"/"Cesar") o el original.
    La resolucion a un objeto User (responsable es FK) se hace en el importador.
    """
    t = str(raw or "").lower()
    if "cami" in t:
        return "Camila"
    if "cesar" in t or "cés" in t:
        return "Cesar"
    return raw or ""


def norm_sub_estado(estado, sub_estado):
    """El sub-estado solo tiene sentido en los estados 7 y 8; si no, se limpia."""
    if estado in (choices.ESTADO_NO_VIABLE, choices.ESTADO_NO_AVANZO):
        return sub_estado or ""
    return ""
