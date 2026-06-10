# Phase 9 research — ML residual stress model (SBIR track)

Standalone research pipeline. Not deployed, never imported by `backend/`.
Stdlib-only so far — no extra requirements.

## Idea

AquaCrop is a generic physics simulation; its days-to-stress error on a
given farm is systematic, not random. We train a model to predict that
error (the *residual*) from AquaCrop output + micro-climate + soil +
crop history. Final prediction = physics + learned correction.

With no pilot farmers yet, instrumented public stations act as
pseudo-farms: NRCS SCAN stations measure daily soil moisture at
2/4/8/20/40 in — ground truth to compare AquaCrop's simulated root-zone
depletion against. ~183 stations × 10+ years ≈ thousands of
station-seasons.

## Pipeline

| step | script | output |
|---|---|---|
| 1. station inventory | `scan_inventory.py` | `data/scan_stations.csv` — 197 SCAN stations with daily SMS, depth + date coverage |
| 2. crop labels | `cdl_crop_labels.py` | `data/scan_stations_crops.csv` — CDL class per station per year (2019–2023) + majority vote |
| 3. soil moisture pull | `scan_pull_sms.py` | `data/sms/<station>.csv` — full daily SMS history, ag stations only |
| 4. AquaCrop runs | TODO | per station-season simulated depletion |
| 5. residual dataset | TODO | AquaCrop prediction vs SMS-derived truth + features (gridMET, soil, crop) |
| 6. train + validate | TODO | residual model; MAE vs vanilla AquaCrop, held out **by station** |

## Data sources (all free)

- **NRCS AWDB REST** (no key): station metadata + daily SMS.
  https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html
  Quirk: `stationTriplets=*:*:SCAN` is rejected — query per state.
- **NASS CropScape CDL** (no key): point query needs EPSG:5070 (CONUS
  Albers) — `cdl_crop_labels.py` implements the Snyder projection
  formulas to avoid a pyproj dependency.
- **gridMET / PRISM** (no key): gridded daily weather for micro-climate
  features (step 5).
- **AmeriFlux** (free account): flux-tower ET — validation set, not bulk
  training.
- **OpenET**: already integrated in product; watch 100 req/month free
  tier for research pulls — request research tier citing SBIR prep.

## Validation rule

Hold out whole stations, never random rows: same-station rows in train
and test leak the station's systematic bias — the exact thing the model
predicts. Headline metric: days-to-stress MAE vs vanilla AquaCrop.
