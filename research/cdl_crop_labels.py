"""Label SCAN stations with USDA Cropland Data Layer crop types.

Reads research/data/scan_stations.csv (from scan_inventory.py), queries
NASS CropScape for the CDL class at each station for several recent
years, and writes research/data/scan_stations_crops.csv with per-year
classes plus a majority-vote label. Stations sitting in rangeland/forest
get filtered out downstream; stations in cropland become pseudo-farms.

CropScape point service (free, no key) wants CONUS Albers (EPSG:5070)
coordinates, so we project WGS84 lat/lon with Snyder's Albers
equal-area formulas (exact, avoids a pyproj dependency).

Usage: python research/cdl_crop_labels.py
"""

import csv
import math
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

IN_PATH = Path(__file__).parent / "data" / "scan_stations.csv"
OUT_PATH = Path(__file__).parent / "data" / "scan_stations_crops.csv"
CDL_URL = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue"
YEARS = [2019, 2020, 2021, 2022, 2023]

# GRS80 ellipsoid + EPSG:5070 projection constants
GRS80_A = 6378137.0
GRS80_E2 = 0.00669438002290
LAT_0, LON_0 = math.radians(23.0), math.radians(-96.0)
SP_1, SP_2 = math.radians(29.5), math.radians(45.5)


def _q(lat: float) -> float:
    e = math.sqrt(GRS80_E2)
    sin_lat = math.sin(lat)
    return (1 - GRS80_E2) * (
        sin_lat / (1 - GRS80_E2 * sin_lat**2)
        - (1 / (2 * e)) * math.log((1 - e * sin_lat) / (1 + e * sin_lat))
    )


def _m(lat: float) -> float:
    return math.cos(lat) / math.sqrt(1 - GRS80_E2 * math.sin(lat) ** 2)


def wgs84_to_albers(lat_deg: float, lon_deg: float) -> tuple[float, float]:
    """Snyder (1987) eq. 14-1..14-4: forward Albers equal-area conic."""
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    m1, m2 = _m(SP_1), _m(SP_2)
    q0, q1, q2 = _q(LAT_0), _q(SP_1), _q(SP_2)
    n = (m1**2 - m2**2) / (q2 - q1)
    big_c = m1**2 + n * q1
    rho = GRS80_A * math.sqrt(big_c - n * _q(lat)) / n
    rho0 = GRS80_A * math.sqrt(big_c - n * q0) / n
    theta = n * (lon - LON_0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def fetch_cdl_category(x: float, y: float, year: int) -> str:
    params = urllib.parse.urlencode({"year": year, "x": round(x), "y": round(y)})
    request = urllib.request.Request(f"{CDL_URL}?{params}")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode()
            match = re.search(r'category:\s*"([^"]*)"', body)
            return match.group(1) if match else ""
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                return ""
            time.sleep(5)
    return ""


def main() -> None:
    stations = list(csv.DictReader(IN_PATH.open()))
    print(f"{len(stations)} stations x {len(YEARS)} years")

    rows = []
    for i, station in enumerate(stations, 1):
        x, y = wgs84_to_albers(
            float(station["latitude"]), float(station["longitude"])
        )
        categories = {
            year: fetch_cdl_category(x, y, year) for year in YEARS
        }
        votes = Counter(c for c in categories.values() if c)
        majority = votes.most_common(1)[0][0] if votes else ""
        rows.append(
            {
                **station,
                **{f"cdl_{year}": categories[year] for year in YEARS},
                "cdl_majority": majority,
            }
        )
        print(f"[{i}/{len(stations)}] {station['station_triplet']} -> {majority}")
        time.sleep(0.2)

    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nwrote {OUT_PATH}")
    print("majority-class counts:")
    for category, count in Counter(r["cdl_majority"] for r in rows).most_common(15):
        print(f"  {count:4d}  {category or '(no data)'}")


if __name__ == "__main__":
    main()
