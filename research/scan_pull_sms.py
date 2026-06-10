"""Pull daily soil-moisture series for ag-relevant SCAN stations.

Reads research/data/scan_stations_crops.csv (from cdl_crop_labels.py),
keeps stations whose majority CDL class looks like cropland, and pulls
the full daily SMS history at every depth from the AWDB REST API.
Output: one CSV per station in research/data/sms/<station_id>_<state>.csv
with columns date, sms_<depth>in.

These series are the ground truth the residual model trains against:
AquaCrop-predicted root-zone depletion vs measured profile moisture.

Usage: python research/scan_pull_sms.py
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"
IN_PATH = Path(__file__).parent / "data" / "scan_stations_crops.csv"
OUT_DIR = Path(__file__).parent / "data" / "sms"

# CDL classes that can't be simulated as a crop — station gets dropped.
# Strings must match CropScape's exact category labels (verified against
# the step-2 majority-class output).
NON_AG_CLASSES = {
    "",
    "Shrubland",
    "Grass/Pasture",
    "Deciduous Forest",
    "Evergreen Forest",
    "Mixed Forest",
    "Barren",
    "Open Water",
    "Woody Wetlands",
    "Herbaceous Wetlands",
    "Developed/Open Space",
    "Developed/Low Intensity",
    "Developed/Medium Intensity",
    "Developed/High Intensity",
    "Fallow/Idle Cropland",
}


def fetch_sms(triplet: str, begin: str, end: str) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "stationTriplets": triplet,
            "elements": "SMS:*:*",
            "duration": "DAILY",
            "beginDate": begin,
            "endDate": end,
        }
    )
    request = urllib.request.Request(
        f"{DATA_URL}?{params}", headers={"Accept": "application/json"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.load(response)
            return payload[0]["data"] if payload else []
        except (TimeoutError, urllib.error.URLError) as err:
            if attempt == 2:
                raise
            print(f"  retry {attempt + 1} after {err}")
            time.sleep(10)
    return []


def series_to_rows(data: list[dict]) -> tuple[list[str], list[dict]]:
    """Pivot per-depth series into one row per date."""
    by_date: dict[str, dict[str, float]] = {}
    depths = set()
    for element in data:
        depth = abs(element["stationElement"]["heightDepth"])
        column = f"sms_{depth}in"
        depths.add(column)
        for point in element["values"]:
            if point.get("value") is not None:
                by_date.setdefault(point["date"], {})[column] = point["value"]

    columns = ["date"] + sorted(depths, key=lambda c: int(c[4:-2]))
    rows = [
        {"date": day, **values} for day, values in sorted(by_date.items())
    ]
    return columns, rows


def main() -> None:
    stations = [
        s
        for s in csv.DictReader(IN_PATH.open())
        if s["cdl_majority"] not in NON_AG_CLASSES
    ]
    print(f"{len(stations)} ag stations to pull")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, station in enumerate(stations, 1):
        triplet = station["station_triplet"]
        out_path = OUT_DIR / f"{triplet.replace(':', '_')}.csv"
        if out_path.exists():
            print(f"[{i}/{len(stations)}] {triplet} cached, skip")
            continue

        data = fetch_sms(triplet, station["sms_begin"], station["sms_end"])
        columns, rows = series_to_rows(data)
        if not rows:
            print(f"[{i}/{len(stations)}] {triplet} returned no data")
            continue

        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        print(
            f"[{i}/{len(stations)}] {triplet} ({station['cdl_majority']}): "
            f"{len(rows)} days -> {out_path.name}"
        )
        time.sleep(1)


if __name__ == "__main__":
    main()
