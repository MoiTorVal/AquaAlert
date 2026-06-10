"""Build a pseudo-farm candidate inventory from NRCS SCAN stations.

Phase 9 (ML residual model) needs ground-truth soil moisture to stand in
for farms we don't have yet. Each SCAN station with daily soil moisture
(SMS) is one candidate site. Output: research/data/scan_stations.csv,
one row per station with depth coverage and data date range.

API: AWDB REST (no key) — https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html
The stations endpoint rejects a fully wild triplet (*:*:SCAN), so we
query one state at a time.

Usage: python research/scan_inventory.py
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

BASE_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"
OUT_PATH = Path(__file__).parent / "data" / "scan_stations.csv"

CONUS_STATES = [
    "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "IA", "ID", "IL",
    "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT",
    "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY",
]

# endDate 2100-01-01 means "still collecting"
ONGOING_SENTINEL = "2100"


def fetch_state_stations(state: str) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "stationTriplets": f"*:{state}:SCAN",
            "returnStationElements": "true",
            "activeOnly": "false",
        }
    )
    request = urllib.request.Request(
        f"{BASE_URL}?{params}", headers={"Accept": "application/json"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as err:
            # 400 = no stations matched for this state; anything else is real
            if err.code == 400:
                return []
            raise
        except (TimeoutError, urllib.error.URLError) as err:
            if attempt == 2:
                raise
            print(f"{state}: retry {attempt + 1} after {err}")
            time.sleep(5)
    return []


def summarize_station(station: dict) -> dict | None:
    daily_sms = [
        el
        for el in station.get("stationElements", [])
        if el["elementCode"] == "SMS" and el["durationName"] == "DAILY"
    ]
    if not daily_sms:
        return None

    depths_in = sorted({abs(el["heightDepth"]) for el in daily_sms})
    begin = min(el["beginDate"] for el in daily_sms)[:10]
    end = max(el["endDate"] for el in daily_sms)[:10]
    if end.startswith(ONGOING_SENTINEL):
        end = date.today().isoformat()
    years = round(
        (date.fromisoformat(end) - date.fromisoformat(begin)).days / 365.25, 1
    )

    return {
        "station_triplet": station["stationTriplet"],
        "name": station["name"],
        "state": station["stateCode"],
        "county": station.get("countyName", ""),
        "latitude": station["latitude"],
        "longitude": station["longitude"],
        "elevation_ft": station.get("elevation", ""),
        "huc": station.get("huc", ""),
        "sms_depths_in": "|".join(str(d) for d in depths_in),
        "sms_begin": begin,
        "sms_end": end,
        "sms_years": years,
    }


def main() -> None:
    rows = []
    for state in CONUS_STATES:
        stations = fetch_state_stations(state)
        kept = [s for s in (summarize_station(st) for st in stations) if s]
        print(f"{state}: {len(stations)} stations, {len(kept)} with daily SMS")
        rows.extend(kept)
        time.sleep(0.5)

    rows.sort(key=lambda r: (-r["sms_years"], r["state"]))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{len(rows)} candidate stations -> {OUT_PATH}")
    print(f"with >=5y of daily SMS: {sum(1 for r in rows if r['sms_years'] >= 5)}")


if __name__ == "__main__":
    main()
