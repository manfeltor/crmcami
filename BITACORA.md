# Bitácora — CRM Intralog

Registro narrativo de **qué se hizo y por qué**, para complementar el `git log`
(que es más seco). Convención: una entrada por hito, la más reciente arriba.

## Roadmap
- [x] **Paso 0** — Esqueleto Django (`accounts` + login + config de prod)
- [~] **Paso 1** — Servir el SPA (`crm_mock.html`) desde Django detrás de login
- [ ] **Paso 2** — Modelo de datos (app `crm`: Lead / LeadHistorial / TallyNoComercial + normalización)
- [ ] **Paso 3** — Lecturas (GET) + conectar `DataAPI.loadX` a `fetch()`
- [ ] **Paso 4** — Escrituras (POST) + conectar `save`/`bulk`/`delete`/`bump`/`import`
- [ ] **Paso 5** — Ingesta WordPress (pull, app `integrations`)
- [ ] **Paso 6** — Deploy Cloud Run + Cloud SQL

## Arquitectura (resumen)
- **Django + MySQL** (Cloud SQL en prod) + **Cloud Run**.
- **Frontend** = SPA de un solo archivo (`crmcami/frontend/crm_mock.html`), servido **crudo**
  detrás de `login_required`. Se conecta al backend **feature por feature**, cambiando cada
  método del `DataAPI` (hardcodeado → `fetch`/`POST`). La app nunca queda a medias.
- **Auth**: session nativa de Django, custom User vacío (`accounts.User`).

---

## Entradas

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
