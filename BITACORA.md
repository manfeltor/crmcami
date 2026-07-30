# Bitácora — CRM Intralog

Registro narrativo de **qué se hizo y por qué**, para complementar el `git log`
(que es más seco). Convención: una entrada por hito, la más reciente arriba.

## Roadmap
- [x] **Paso 0** — Esqueleto Django (`accounts` + login + config de prod)
- [x] **Paso 1** — Servir el SPA (`crm_mock.html`) desde Django detrás de login
- [x] **Paso 2** — Modelo de datos (app `crm`: Lead / LeadHistorial / TallyNoComercial + normalización)
- [x] **Paso 3** — Lecturas (GET) + conectar `DataAPI.loadLeads` a `fetch()`
- [x] **Paso 4** — Escrituras (POST) + conectar `save`/`bulk`/`delete`/`bump`/`import`
- [x] **Paso 5** — Ingesta WordPress (pull, app `integrations`)
- [~] **Paso 6** — Deploy Cloud Run + Cloud SQL (imagen + ensayo local ✓; deploy a la nube lo hace el user)

## Arquitectura (resumen)
- **Django + MySQL** (Cloud SQL en prod) + **Cloud Run**.
- **Frontend** = SPA de un solo archivo (`crmcami/frontend/crm_mock.html`), servido **crudo**
  detrás de `login_required`. Se conecta al backend **feature por feature**, cambiando cada
  método del `DataAPI` (hardcodeado → `fetch`/`POST`). La app nunca queda a medias.
- **Auth**: session nativa de Django, custom User vacío (`accounts.User`).

---

## Entradas

### 2026-07-30 — Paso 6 (a/b): Dockerfile + WhiteNoise + docker-compose (ensayo local)
- **WhiteNoise** en settings (middleware + `STATIC_ROOT` + `STORAGES` CompressedManifest). NO nginx:
  Cloud Run ya es el reverse proxy/TLS; whitenoise cubre los estáticos. `SECURE_SSL_REDIRECT` y
  `CSRF_TRUSTED_ORIGINS` override por env (para el ensayo local con DEBUG=False).
- **Dockerfile** single-stage (sin Node — el SPA se sirve crudo): libs SO para mysqlclient,
  `pip install`, `collectstatic` en build (creds dummy), gunicorn en `$PORT`.
- **docker-compose.yml** = ensayo local (app en modo prod + MySQL en contenedor) = "mini Cloud Run".
- **Verificado**: build OK (mysqlclient compila), migraciones **contra MySQL** OK, superuser +
  gunicorn + `GET /login/` 200, `seed_demo` (9 leads). **Imagen deploy-ready.**
- El deploy real a Cloud Run + Cloud SQL (Cloud SQL instance, Secret Manager, migrar por proxy,
  `gcloud run deploy`) lo hace el user (tiene experiencia en GCP).

### 2026-07-28 — Paso 5: ingesta WordPress (pull) — el CRM recibe leads del sitio
- App `integrations`: `client` (urllib + Basic Auth con WP App Password), `mapper` (config por
  form 3/4/5 — los campos difieren), `services` (sync con **marca de agua forward-only** + dedup por
  `wp_entry_id` + resiliente a filas malas), `SyncState`, command `sync_wp_leads`.
- Descubrimiento: `scripts/wp_discovery.py` (App Password, sin volcar PII). Forms activos = **3/4/5**
  (Formidable). Servicio: form 3 del campo, form 4→Cross-docking, form 5→Almacenamiento. **Corte: 1-ene-2026.**
- Disparo desde el SPA: **sync throttled al cargar** (15 min) + botón **"Sincronizar"** (force).
  Todo por acción, **sin jobs async** (compatible con cold start / min-instances=0).
- Verificado en vivo: **70 leads** desde enero; un lead borrado **NO reaparece** (forward-only);
  bug `servicio` > 40 chars corregido (valida contra choices). Auth por App Password sirve también para prod.

### 2026-07-28 — Paso 4: escrituras conectadas (el CRM ya persiste)
- **CSRF**: `@ensure_csrf_cookie` en la vista del SPA + helpers `getCookie`/`postJSON`
  (header `X-CSRFToken` en cada POST). Sin token → 403.
- **Endpoints POST**: crear/editar (`/api/leads/`, `/api/leads/<id>/`), `bulk-estado`,
  `bulk-delete`, `tally` (+/-), `import` (reemplaza todo). El historial y el cambio de
  estado los arma el **servidor** (no el cliente); `responsable` mapeado del nombre al User.
- **Mock**: `DataAPI.saveLead/bulkEstado/bulkDelete/bumpTally/importLeads`; `save`,
  `applyBulkEstado`, `bulkDelete`, `bump`, `onFile` conectados con re-fetch. `loadTally`→`fetch`.
- Verificado con CSRF real (test client). **Todas las escrituras persisten en MySQL.**

### 2026-07-28 — Paso 3: lecturas conectadas (`GET /api/leads/`)
- Endpoint `GET /api/leads/` (JsonResponse, `login_required`) que serializa los `Lead`
  con las claves que el mock ya consume (`subOrigen`/`estadoFecha`/`historial[{ts,text}]`).
- Command `seed_demo` con los 9 leads ficticios (dev, sin PII).
- Mock: `DataAPI.loadLeads()` pasa de `return SEED` a `fetch()`; `rows` arranca en `[]`
  y se llena en un `useEffect` (sync→async). **El SPA ya muestra data real de MySQL.**
- Las escrituras siguen en memoria → Paso 4. Verificado en browser (9 leads).

### 2026-07-28 — Paso 2: modelo de datos (app `crm`)
- Modelos `Lead`, `LeadHistorial` (reemplaza el array `historial[]`), `TallyNoComercial`.
- `comentarios` = **propiedad derivada** del historial (no es columna) → una sola fuente de verdad.
- `responsable` FK→User; enums en `crm/choices.py`; normalización en `crm/normalize.py`
  (fuente única para import y sync WP); `wp_entry_id` unique para el pull de Formidable.
- Migrado a MySQL (`crm_lead` / `crm_leadhistorial` / `crm_tallynocomercial`). Lógica
  verificada con un lead de prueba + rollback (comentarios derivado, alerta +30d, FK responsable).

### 2026-07-17 — Paso 1: servir el SPA desde Django
- `crm_mock.html` movido a `crmcami/frontend/`.
- Vista `spa` (`crmcami/views.py`) que lo sirve **crudo** con `FileResponse`, detrás de
  `login_required` (no vía template engine: el JSX usa `{{ }}` que Django malinterpretaría).
- `/` ahora sirve el SPA; se elimina el placeholder `home.html`.
- Sin endpoints todavía: muestra la **data ficticia** del SEED. Próximo: Paso 2.

### 2026-07-21 — Login (commit `9837ca9`)
- Session auth nativa: `LoginView`/`LogoutView` + template propio + settings `LOGIN_*`.
- Home protegida con `login_required`. Flujo completo verificado (anónimo→login, logout POST).

### 2026-07-22 — Primer migrate (commit `cf8638c`)
- `accounts.User` (AbstractUser vacío) migrado a MySQL. Superuser creado.
- Carpetas `static/` y `templates/` + fix `STATICFILES_DIRS` (warning W004).

### 2026-07-22 — Config MySQL prod-ready (commit `446d04f`)
- `DATABASES` MySQL (utf8mb4, STRICT_TRANS_TABLES, CONN_MAX_AGE=0); mismo bloque local/prod
  (prod = socket Cloud SQL vía `DB_HOST=/cloudsql/...`).
- Hardening: cookies SECURE + SSL redirect atados a `not DEBUG`, `SECURE_PROXY_SSL_HEADER`,
  `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` vía `APPHOST`.
- Fix `DEBUG = config('DEBUG', default=False, cast=bool)` (evita DEBUG=True fantasma en prod).

### 2026-07-27 — Setup inicial (commit `316805b`)
- Proyecto Django `crmcami` + app `accounts`.
- `crm_mock.html`: frontend vibecodeado portado a **cascarón sin persistencia** (DataAPI shim,
  data ficticia anonimizada). Repo git + `.gitignore` de batalla; PII y secretos fuera del repo.
