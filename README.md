# AquaAlert — crop water-stress alerts for small farms

[![CI](https://github.com/MoiTorVal/AquaAlert/actions/workflows/ci.yml/badge.svg)](https://github.com/MoiTorVal/AquaAlert/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/python-3.13-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**[Live demo →](https://aqua-alert-pearl.vercel.app)** &nbsp;·&nbsp; [API docs](https://aquaalert-production.up.railway.app/docs)

AquaAlert warns small farm operators when a field is approaching water stress, and tracks the water, energy, and CO₂ they save for grant and SGMA reporting. It is **alert-based, not an irrigation scheduler**: every field gets a green / yellow / red severity plus a "days to stress" estimate so a grower without an agronomist can see what needs attention today.

> [!IMPORTANT]
> **Not a substitute for an agronomist or field scouting.** Stress estimates come from a crop-water-balance model driven by satellite data, not from sensors in the ground. Satellite inputs lag ~5–7 days; every data-derived figure in the UI is labeled "as of [date]." Use it as a prioritization signal and confirm in the field.

---

## Features

- **Field boundary capture** — draw a polygon on a satellite map; no GIS skills required.
- **Daily ET + crop simulation** — pulls evapotranspiration per polygon from OpenET; gap-fills the ~5–7 day lag with Spatial CIMIS ETo × FAO-56 Kc; feeds observed rainfall (Open-Meteo) and all of this into AquaCrop-OSPy.
- **Stress alerts** — green / yellow / red severity with a linear days-to-stress projection. SMS alerts fire only on severity *escalation* — no spam on re-runs.
- **SMS reply-to-log** — reply "1" or "1 5000" to log an irrigation event without opening the app. Reply Y/N to record alert feedback for model improvement.
- **Irrigation event log** — manual or SMS-sourced entries; runtime or gallons mode; edit and delete.
- **Water savings** — gallons saved vs. a user-provided baseline → pump kWh → CO₂ avoided; ready for SGMA and grant reporting.
- **SGMA export** — per-farm CSV and PDF reports.
- **Public impact dashboard** — aggregate water, energy, and CO₂ numbers, no login required.
- **Bilingual SMS copy** — all alert and reply messages in English and Spanish.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2, Alembic, APScheduler |
| Database | PostgreSQL + PostGIS |
| Auth | JWT HS256 + rotating refresh tokens, bcrypt, HttpOnly cookies |
| Frontend | Next.js 16 (App Router), React 19, TypeScript 5, Tailwind 4 |
| Crop model | AquaCrop-OSPy (UN FAO official Python port) |
| ET actuals | OpenET API |
| ET gap-fill | Spatial CIMIS (ETo × FAO-56 Kc; provisional rows replaced when actuals arrive) |
| Rainfall | Open-Meteo (CC BY 4.0) |
| SMS | Twilio via raw REST (httpx; no SDK) |
| Maps | Leaflet + leaflet-draw |
| Tests | pytest + testcontainers (real PostGIS), vitest + eslint |
| CI | GitHub Actions (97% coverage gate) |

**Supported crops:** alfalfa, barley, cassava, corn/maize, cotton, dry bean, potato, quinoa, rice, sorghum, soybean, sugar beet, sunflower, tomato, wheat.

---

## Engineering decisions

### 1. Escalation-only SMS alerts

Sending an alert every time the scheduler runs would flood a farmer's phone on consecutive red-stress days. Instead, `Alert` rows are deduped on `(farm_id, as_of_date, severity)` and SMS fires only when severity *increases* (green→yellow, yellow→red). A Twilio failure is logged but never fails the farm's daily job — one transient SMS error should not abort ET pulls and sim runs for every other farm.

### 2. Provisional ET gap-fill instead of blank data

OpenET actuals have a ~5–7 day lag. Rather than showing stale or missing readings, the scheduler inserts provisional Spatial CIMIS ETo × Kc rows (tagged `source="cimis:eto*kc"`) for each lag day, and *replaces them in place* when the OpenET actual arrives. The API exposes `et_latest_actual_date` so the UI can surface an "estimated" badge for the provisional window.

### 3. Refresh token rotation with reuse detection

Access tokens expire in 15 minutes. Refresh tokens are single-use: each use issues a new token and invalidates the previous one. If a token is reused — a strong signal of theft — the entire token family is revoked (all sessions for that user logged out). Tokens are stored as SHA-256 hashes, so a database breach exposes nothing usable.

### 4. Real Postgres in CI via testcontainers

The test suite spins up a live `postgis/postgis:16-3.4` container for every pytest run and executes `alembic upgrade head` as part of the fixture. This catches spatial query bugs, migration chain errors, and schema regressions that mock databases miss — and it means CI exercises the exact migration path that runs on Railway at deploy time.

---

## Getting started

Requires Python 3.13, Node 24, Docker (for tests), and a PostgreSQL + PostGIS instance.

```bash
# 1. Configure
cp .env.example .env          # fill in real values

# 2. Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head          # Alembic owns all schema changes
uvicorn backend.main:app --reload

# 3. Frontend
cd frontend && npm install && npm run dev

# 4. Tests (requires Docker)
pytest --cov=backend --cov-fail-under=97
```

Key environment variables:

| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://…` — takes precedence over discrete `DB_*` vars. Railway exposes this as `postgres://`; the app normalizes the scheme automatically. |
| `SECRET_KEY` | 32+ character random string for JWT signing. |
| `COOKIE_SAMESITE` | Set to `none` in production (cross-domain Railway + Vercel deploy). Requires `SECURE_COOKIE=true`. |
| `SCHEDULER_ENABLED` | Set `true` on **exactly one** process. APScheduler has no cross-process lock — two workers = two SMS sends per alert. |
| `OPENET_API_KEY` | Optional — ET fetch disabled if unset. |
| `CIMIS_APP_KEY` | Optional — CIMIS gap-fill disabled if unset. |
| `TWILIO_*` | Optional — SMS disabled if unset. |

Health check: `GET /healthz` → `{"status":"ok"}` (200) or `{"status":"error","detail":"…"}` (503).

---

## Data sources & citations

- **OpenET** — daily ET per field polygon, CONUS-only, ~5–7 day lag. <https://openetdata.org>
- **Spatial CIMIS** — California reference ETo at any coordinate, ~1-day lag. <https://et.water.ca.gov>
- **Open-Meteo** — daily precipitation for AquaCrop rainfall input. Open data, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). <https://open-meteo.com>
- **AquaCrop-OSPy** — UN FAO crop-water-balance model, official Python port. <https://github.com/aquacropos/aquacrop>
- **CO₂ factor** — EPA eGRID2022, CAMX (California) subregion: ~498 lb CO₂/MWh = 0.226 kg CO₂/kWh. <https://www.epa.gov/egrid>
- **Pump energy** — gallons → kWh via lift head and 0.55 overall pumping-plant efficiency (NRCS field average).

---

## Security

- Passwords bcrypt-hashed; JWTs HS256, delivered in HttpOnly cookies.
- Rotating refresh tokens with reuse detection revoke all sessions on token theft — see [Engineering decisions §3](#3-refresh-token-rotation-with-reuse-detection).
- `SameSite=None; Secure` in production for cross-domain deploys; `SameSite=Lax` in local dev.
- Per-IP rate limiting (slowapi): auth endpoints 5 req/min, default 60 req/min.
- All config via environment variables; no secrets in source.
- Voluntary equity self-ID fields (socially disadvantaged, beginning farmer) are never required and never exposed in aggregate without anonymization.

---

## Known limitations / next steps

| Limitation | Notes |
|---|---|
| **No email delivery** | Password reset tokens are log-only (`LOG_RESET_LINKS=true`). Email (SendGrid) is a documented gap; SMS shipped as the first delivery channel. |
| **No phone OTP verification** | A typo in a phone number causes silent non-delivery. OTP is the next auth hardening item. |
| **English-only web UI** | SMS alert copy is bilingual (EN/ES). Full `next-intl` wiring is the next i18n step. |
| **OpenET free tier** | 100 req/month (~3 farms at daily pulls). The demo account uses pre-baked fixture data and does not call the live OpenET API. |
| **Signup reveals account existence** | `400 "Email already registered"` is a minor account-enumeration vector. Fix is deferred until email delivery ships (neutral message + confirmation flow). |
| **Single-region** | OpenET is CONUS-only; CIMIS is California-only. Multi-region requires a different ET source. |

---

## License

MIT — see [LICENSE](LICENSE).
