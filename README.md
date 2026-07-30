# CRM Intralog

CRM comercial de **Intralog Argentina**, portado de una herramienta de un solo
archivo HTML (React vbcoded, sin backend) a una app **Django + MySQL**
lista para **Cloud Run + Cloud SQL**, con ingesta automática de leads desde el
sitio en **WordPress**.

> Registro narrativo del desarrollo (qué se hizo y por qué) en **[`BITACORA.md`](BITACORA.md)**.

---

## Arquitectura

- **Django 6 + MySQL** (Cloud SQL en prod) desplegado en **Cloud Run** (serverless,
  arranque en frío / `min-instances=0`).
- **Frontend = SPA de un solo archivo** (`crmcami/frontend/crm_mock.html`): se sirve
  **crudo** (con `FileResponse`) detrás de `login_required`. Toda la lectura/escritura
  de datos pasa por un único objeto **`DataAPI`** en el JS, que llama a la API JSON de
  Django (`fetch`/`POST` con CSRF). No hay build de Node: React/Tailwind vienen de CDN.
- **Ingesta WordPress (pull)**: Django consulta un plugin REST del sitio (Formidable
  Forms) y trae los leads nuevos. Disparo **por acción** (al cargar el SPA, throttled, +
  botón "Sincronizar") — **sin jobs async**, compatible con arranque en frío.
- **Auth**: sesión nativa de Django, usuario custom (`accounts.User`).

### Apps
| App | Qué hace |
|---|---|
| `accounts` | Usuario custom (`AbstractUser`). |
| `crm` | `Lead`, `LeadHistorial`, `TallyNoComercial` + API JSON + normalización. |
| `integrations` | Pull de WordPress (Formidable): client, mapper, sync con marca de agua. |

---

## Estructura

    crm_cami/                     # raíz del repo
    ├── crmcami/                  # proyecto Django (se despliega esto)
    │   ├── manage.py
    │   ├── requirements.txt
    │   ├── Dockerfile · docker-compose.yml · .dockerignore
    │   ├── crmcami/              # settings, urls, wsgi, authvars (config por env)
    │   ├── accounts/ crm/ integrations/
    │   ├── frontend/crm_mock.html   # el SPA
    │   ├── templates/  static/
    ├── scripts/wp_discovery.py   # descubrimiento de los forms de WordPress
    ├── .env                      # config/secretos (NO se versiona)
    └── BITACORA.md

---

## Desarrollo local

Requisitos: Python 3.12, MySQL corriendo local (o usar el compose, ver abajo).

```bash
# 1. venv + deps
python -m venv crmcamienv && source crmcamienv/bin/activate
pip install -r crmcami/requirements.txt

# 2. config: copiar la plantilla y completar
cp .env.example .env      # editar DB_*, SECRET_KEY, WP* ...

# 3. base + datos
cd crmcami
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo          # 9 leads ficticios (opcional)

# 4. correr
python manage.py runserver          # http://localhost:8000
```

### Ensayo con Docker (recomendado antes de deployar)
Levanta la **imagen real en modo prod** (gunicorn, `DEBUG=False`, WhiteNoise) contra un
MySQL en contenedor — un "mini Cloud Run":

```bash
cd crmcami
docker compose up --build           # http://localhost:8080  (admin / admin1234)
docker compose exec web python manage.py seed_demo
docker compose down
```

---

## Variables de entorno

Se leen con `python-decouple` desde `.env` (local) o desde las env vars del servicio
(Secret Manager en Cloud Run). Ver **[`.env.example`](.env.example)**.

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Secret de Django. |
| `DEBUG` | `True` local / `False` prod. |
| `DB_NAME` `DB_USR` `DB_PASS` `DB_HOST` `DB_PORT` | MySQL. En prod `DB_HOST` = `/cloudsql/PROY:REGION:INSTANCIA` (Django detecta el `/` y usa socket). |
| `APPHOST` | Host del servicio Cloud Run (alimenta `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`). |
| `WPUSER` `WPPASS` | Usuario + **Application Password** de WordPress (Basic Auth). |
| `WPCUSTOMAPISUBM` | URL base del endpoint del plugin (`.../wp-json/custom/v1/form-submissions/`). |
| `SECURE_SSL_REDIRECT` `CSRF_TRUSTED_ORIGINS` | Overrides opcionales (para el ensayo local). |

---

## Integración WordPress

- Sitio en WordPress con **Formidable Forms**. Un plugin custom expone las submissions
  por REST (`custom/v1/form-submissions/<form_id>`), autenticado por **Application Password**.
- Forms activos: **3** (principal del website), **4** (Landing Crossdock → servicio
  Cross-docking), **5** (Landing Fulfillment → Almacenamiento).
- El sync usa una **marca de agua** (mayor id de submission procesado): solo trae lo nuevo
  y **forward-only** → un lead borrado en el CRM no reaparece. Corte inicial: `2026-01-01`.
- Descubrir la estructura de los forms: `python scripts/wp_discovery.py`.

---

## Deploy (Cloud Run + Cloud SQL)

La imagen (`crmcami/Dockerfile`) es la que se despliega. Puntos clave:

1. Crear instancia **Cloud SQL (MySQL)** + base.
2. Cargar secretos en **Secret Manager** (`SECRET_KEY`, `DB_*`, `WP*`, `APPHOST`).
3. **Migraciones**: correr por el **Cloud SQL Auth Proxy** o un Cloud Run Job — **no** en
   el arranque del contenedor (el `CMD` del Dockerfile es solo gunicorn).
4. `gcloud run deploy --add-cloudsql-instances PROY:REGION:INSTANCIA ...` con las env vars.
5. Activar **backups automáticos** en Cloud SQL.

---

## Comandos útiles

```bash
python manage.py seed_demo [--flush]                 # data demo (9 leads ficticios)
python manage.py sync_wp_leads [--dry-run|--force]   # pull de WordPress
```
