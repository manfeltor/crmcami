"""
Descubrimiento de la estructura de los forms de Formidable via el plugin REST.

Llama al endpoint del plugin (custom/v1/form-submissions/<id>) con Basic Auth
(WP Application Password) para los forms comerciales y analiza QUE campos trae
cada uno. NO imprime PII: por cada campo muestra el nombre + un descriptor
seguro (largo, si parece email/telefono), no el valor real.

Uso:  python scripts/wp_discovery.py
Lee de .env: WPUSER, WPPASS (app password), WPCUSTOMAPISUBM (URL base del endpoint).
Usa solo la stdlib (urllib) para no depender de 'requests'.
"""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

from decouple import Config, RepositoryEnv

ENV = Path(__file__).resolve().parent.parent / ".env"
config = Config(RepositoryEnv(str(ENV)))

BASE = config("WPCUSTOMAPISUBM")
USER = config("WPUSER")
PWD = config("WPPASS")

FORMS = {
    # Solo 3/4/5 estan activos (confirmado con mkt). 1/2 (Contact Us) inactivos.
    3: "Formulario principal del website",
    4: "Landing Crossdock",
    5: "Landing Fulfillment",
}


def url_for(form_id):
    return BASE.rstrip("/") + "/" + str(form_id)


def http_get(url):
    req = urllib.request.Request(url)
    cred = base64.b64encode(f"{USER}:{PWD}".encode()).decode()
    req.add_header("Authorization", "Basic " + cred)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def describe(v):
    """Descriptor NO-PII de un valor (para identificar el tipo de campo)."""
    s = str(v).strip()
    tags = []
    if "@" in s and "." in s:
        tags.append("email?")
    digits = sum(c.isdigit() for c in s)
    if len(s) and digits >= 6 and digits >= len(s) * 0.5:
        tags.append("telefono?")
    if len(s) > 60:
        tags.append("texto-largo?")
    tags.append(f"len={len(s)}")
    return " ".join(tags)


for fid, nombre in FORMS.items():
    print("=" * 72)
    print(f"FORM {fid} — {nombre}")
    u = url_for(fid)
    print("  GET", u)
    status, body = http_get(u)
    print("  HTTP", status)
    if status != 200:
        print("  respuesta:", (body or "")[:200])
        continue
    try:
        data = json.loads(body)
    except ValueError:
        print("  respuesta no-JSON:", body[:200])
        continue

    subs = data.get("form_submissions", []) if isinstance(data, dict) else (data or [])
    print(f"  submissions: {len(subs)}")

    campos = {}
    for s in subs:
        if not isinstance(s, dict):
            continue
        for k, v in s.items():
            if k not in campos and str(v).strip():
                campos[k] = v
    print("  campos detectados (nombre -> descriptor):")
    for k, v in campos.items():
        print(f"    - {k!r}: {describe(v)}")
