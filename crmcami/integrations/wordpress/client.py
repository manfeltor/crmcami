"""
Cliente HTTP contra el plugin REST de WordPress (Formidable).

Basic Auth con WP Application Password. Usa solo la stdlib (urllib) para no
depender de 'requests'. Fail-open: ante cualquier error de red lanza
WordPressUnavailable y el caller decide (normalmente: ignorar y reintentar).
"""
import base64
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


class WordPressUnavailable(Exception):
    """WP no contesto / error de red / auth. El caller decide."""


def _url(form_id):
    return settings.WP_API_URL.rstrip("/") + "/" + str(form_id)


def fetch_form(form_id):
    """
    Devuelve la lista de submissions (dicts) de un form. El plugin devuelve 404
    cuando el form no tiene submissions -> lo tratamos como lista vacia.
    """
    if not settings.WP_API_URL or not settings.WP_USER:
        raise WordPressUnavailable("WP no configurado (WP_API_URL / WP_USER)")

    req = urllib.request.Request(_url(form_id))
    cred = base64.b64encode(f"{settings.WP_USER}:{settings.WP_PASS}".encode()).decode()
    req.add_header("Authorization", "Basic " + cred)
    try:
        with urllib.request.urlopen(req, timeout=settings.WP_SYNC_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        logger.warning("WP form %s -> HTTP %s", form_id, e.code)
        raise WordPressUnavailable(f"HTTP {e.code}") from e
    except Exception as e:  # noqa: BLE001
        logger.warning("WP form %s -> %s", form_id, e)
        raise WordPressUnavailable(str(e)) from e

    if isinstance(data, dict):
        return data.get("form_submissions", []) or []
    return data or []
