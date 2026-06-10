# AquaAlert — crop water-stress alerts for small farms

AquaAlert warns small farm operators when a field is approaching water
stress, and tracks the water (and energy, and CO₂) they save over time
for grant and SGMA reporting. It is **alert-based, not an irrigation
scheduler**: every field gets a simple green / yellow / red severity plus
a "days to stress" estimate, so a grower without an agronomist on staff
can see what needs attention today.

Target users: small farm operators (initially California) who manage
their own irrigation. CONUS-only at launch, bounded by OpenET coverage.

> [!IMPORTANT]
> **Not a substitute for an agronomist or for field scouting.** AquaAlert
> estimates stress from a crop-water-balance model driven by satellite
> data; it does not measure your plants. Satellite inputs lag ~5–7 days,
> so every data-derived figure in the app is labeled "as of [date]." Use
> it as a prioritization signal, not as the sole basis for an irrigation
> decision. Always confirm in the field.

## What it does

- Stores farms with a drawn field boundary, crop, soil class, and
  planting date.
- Pulls daily evapotranspiration (ET) per field polygon from **OpenET**.
- Runs **AquaCrop-OSPy** (the FAO crop-water-balance model) to estimate
  root-zone depletion and days-to-stress; results are cached, never run
  on the request path.
- Classifies severity as **green / yellow / red**.
- Computes water saved vs a farmer-provided baseline, then converts
  gallons → pump kWh → CO₂ avoided for reporting.
- Exports SGMA-style CSV and a public aggregate impact dashboard.

## Tech stack

| Layer        | Technology                                              |
|--------------|---------------------------------------------------------|
| Backend      | FastAPI, SQLAlchemy, Alembic                            |
| Database     | PostgreSQL + PostGIS                                     |
| Auth         | JWT (HS256) in an HttpOnly cookie, bcrypt               |
| Frontend     | Next.js 16 (App Router), React 19, TypeScript           |
| ET data      | OpenET API                                              |
| Crop model   | AquaCrop-OSPy                                            |
| Scheduler    | APScheduler (daily ET pull → sim → savings compute)     |
| Maps         | Leaflet + leaflet-draw (field boundary capture)         |

**Supported crops** (AquaCrop mappings): alfalfa, barley, cassava, corn/
maize, cotton, dry bean, potato, quinoa, rice, sorghum, soybean, sugar
beet, sunflower, tomato, wheat.

## Data sources & citations

- **OpenET** — daily ET per field polygon. CONUS-only, ~5–7 day lag.
  <https://openetdata.org>
- **AquaCrop-OSPy** — UN FAO crop-water model, official Python port.
  <https://github.com/aquacropos/aquacrop>
- **CO₂ factor** — EPA eGRID2022, CAMX (California) subregion, ~498 lb
  CO₂/MWh = 0.226 kg CO₂/kWh. <https://www.epa.gov/egrid>
- **Pump energy** — gallons → kWh via lift and an assumed 0.55 overall
  pumping-plant efficiency (field average).
- **Research (Phase 9, SBIR track):** NRCS SCAN soil moisture and USDA
  NASS Cropland Data Layer, used to build a held-out validation set for
  the ML residual-stress model. See [`research/README.md`](research/README.md).

## Getting started

Requires Python 3.13, Node, and a PostgreSQL instance with PostGIS.

```bash
# 1. Configure
cp .env.example .env          # then fill in real values

# 2. Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head          # Alembic owns all schema changes
uvicorn backend.main:app --reload   # run from the repo root

# 3. Frontend
cd frontend && npm install && npm run dev
```

Health check: `GET /healthz` returns `200` with `{"status":"ok"}` when
the database is reachable, `503` when it is not — wire this to your load
balancer.

## Security & hardening

- Passwords hashed with bcrypt; JWTs signed HS256, delivered in an
  HttpOnly, SameSite=Lax cookie (Secure in production).
- Access tokens are short-lived (2h). Full token revocation
  (refresh-token rotation) is deferred — see Known Issues in `CLAUDE.md`.
- Per-IP rate limiting (slowapi): auth-write endpoints 5/min, default
  60/min elsewhere.
- All config via environment variables; no secrets in source.

## Equity & privacy

Voluntary self-ID fields (socially disadvantaged, beginning farmer) are
never required and never exposed in aggregate without anonymization.

## Impact metrics

<!-- TODO: populate from the live impact dashboard once pilot farms are
onboarded. Do not publish fabricated numbers — pull real aggregates from
/impact. Suggested figures: acres monitored, gallons saved, kWh saved,
tCO₂ avoided. -->

_Pilot in progress — metrics will be published from the public impact
dashboard once the first cohort is reporting._

## Funders & partners

<!-- TODO: add funder/partner logos once grants are secured (USDA WETA,
SBIR Phase I) and RCD / UC Cooperative Extension partnerships are
signed. Do not display logos for unsecured or unconfirmed relationships. -->

_Grant track: USDA WETA, SGMA compliance reporting, USDA SBIR Phase I
(ML residual-stress model). Partnerships in development._

## License

TBD.
