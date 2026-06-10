"""Derive water-stress labels from SCAN soil-moisture series.

For each ag station (from scan_pull_sms.py output) this builds the
ground-truth target the residual model learns to predict:

  1. Depth-weight the 5 sensors into one root-zone volumetric moisture.
  2. Per station, estimate field capacity (FC) and wilting point (WP)
     empirically as high/low percentiles of the moisture distribution —
     soils differ, so normalize per station rather than assume texture.
  3. Available-water fraction  AWF = (theta - WP) / (FC - WP),  clipped
     to [0, 1]. This is the same quantity AquaCrop reports as
     root-zone moisture, so the two are directly comparable.
  4. A stress event = AWF crosses below the management-allowed-depletion
     threshold (MAD, default 0.5 → "50% of available water used").
  5. Within each Apr–Oct growing season, days_to_stress = days from the
     season's first well-watered day until the first stress crossing.

Output: research/data/stress_labels.csv, one row per station-season —
the supervised target for step 6, with AquaCrop's own days_to_stress
to be joined in later as the baseline to beat.

Usage: python research/extract_stress_labels.py
"""

import csv
from datetime import date
from pathlib import Path

SMS_DIR = Path(__file__).parent / "data" / "sms"
OUT_PATH = Path(__file__).parent / "data" / "stress_labels.csv"
CROPS_PATH = Path(__file__).parent / "data" / "scan_stations_crops.csv"

# Representative thickness (inches) each sensor stands for in a 0-40in
# root zone — used as depth weights for the profile average.
DEPTH_WEIGHTS = {
    "sms_2in": 3,
    "sms_4in": 3,
    "sms_8in": 8,
    "sms_20in": 16,
    "sms_40in": 10,
}
FC_PERCENTILE = 95  # wettest stable state ~ field capacity
WP_PERCENTILE = 5   # driest observed ~ wilting point
MAD = 0.5           # management-allowed depletion (RAW threshold)
WELL_WATERED_AWF = 0.8  # season "start" once profile refills above this
SEASON_START, SEASON_END = 4, 10  # April–October


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    rank = (pct / 100) * (len(sorted_values) - 1)
    low = int(rank)
    if low + 1 >= len(sorted_values):
        return sorted_values[-1]
    frac = rank - low
    return sorted_values[low] * (1 - frac) + sorted_values[low + 1] * frac


def root_zone_moisture(row: dict) -> float | None:
    total_weight = 0.0
    weighted = 0.0
    for column, weight in DEPTH_WEIGHTS.items():
        value = row.get(column)
        if value:
            weighted += float(value) * weight
            total_weight += weight
    # require at least the upper+mid profile present
    return weighted / total_weight if total_weight >= 20 else None


def load_series(path: Path) -> list[tuple[date, float]]:
    series = []
    for row in csv.DictReader(path.open()):
        theta = root_zone_moisture(row)
        if theta is not None:
            series.append((date.fromisoformat(row["date"]), theta))
    return series


def station_thresholds(series: list[tuple[date, float]]) -> tuple[float, float]:
    values = sorted(theta for _, theta in series)
    return percentile(values, FC_PERCENTILE), percentile(values, WP_PERCENTILE)


def season_label(
    season_days: list[tuple[date, float]], fc: float, wp: float
) -> dict | None:
    """days_to_stress from first well-watered day to first MAD crossing."""
    if fc <= wp:
        return None
    start_idx = None
    for i, (_, theta) in enumerate(season_days):
        awf = (theta - wp) / (fc - wp)
        if awf >= WELL_WATERED_AWF:
            start_idx = i
            break
    if start_idx is None:
        return None

    start_day = season_days[start_idx][0]
    min_awf = 1.0
    for day, theta in season_days[start_idx:]:
        awf = max(0.0, min(1.0, (theta - wp) / (fc - wp)))
        min_awf = min(min_awf, awf)
        if awf < (1 - MAD):
            return {
                "season_start": start_day.isoformat(),
                "stress_date": day.isoformat(),
                "days_to_stress": (day - start_day).days,
                "reached_stress": 1,
                "season_min_awf": round(min_awf, 3),
            }
    return {
        "season_start": start_day.isoformat(),
        "stress_date": "",
        "days_to_stress": "",
        "reached_stress": 0,
        "season_min_awf": round(min_awf, 3),
    }


def main() -> None:
    crops = {
        r["station_triplet"]: r["cdl_majority"]
        for r in csv.DictReader(CROPS_PATH.open())
    }

    rows = []
    for path in sorted(SMS_DIR.glob("*.csv")):
        triplet = path.stem.replace("_", ":")
        series = load_series(path)
        if len(series) < 365:
            continue
        fc, wp = station_thresholds(series)

        by_year: dict[int, list[tuple[date, float]]] = {}
        for day, theta in series:
            if SEASON_START <= day.month <= SEASON_END:
                by_year.setdefault(day.year, []).append((day, theta))

        for year, season_days in sorted(by_year.items()):
            if len(season_days) < 60:
                continue
            label = season_label(season_days, fc, wp)
            if label is None:
                continue
            rows.append(
                {
                    "station_triplet": triplet,
                    "crop": crops.get(triplet, ""),
                    "year": year,
                    "fc_pct": round(fc, 1),
                    "wp_pct": round(wp, 1),
                    **label,
                }
            )

    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    reached = [r for r in rows if r["reached_stress"] == 1]
    print(f"{len(rows)} station-seasons -> {OUT_PATH}")
    print(f"  reached stress: {len(reached)} ({len(reached) * 100 // len(rows)}%)")
    if reached:
        dts = sorted(r["days_to_stress"] for r in reached)
        print(f"  days_to_stress: min {dts[0]}, median {dts[len(dts) // 2]}, max {dts[-1]}")
    stations = {r["station_triplet"] for r in rows}
    print(f"  across {len(stations)} stations")


if __name__ == "__main__":
    main()
