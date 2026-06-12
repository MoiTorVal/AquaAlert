"""Demo seed helpers (sync SQLAlchemy only)."""
import argparse
import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend import crud
from backend.database import SessionLocal


GRID_SIZE = 30


def _date_range_every_five_days(start: date, end: date) -> list[date]:
    dates: list[date] = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=5)
    return dates


def _mean_ndvi_for_progress(progress: float) -> float:
    # Healthy (0.65-0.80) -> yellow (0.45-0.55) -> red (<0.30)
    if progress < 0.5:
        return 0.8 - progress * 0.3
    if progress < 0.8:
        t = (progress - 0.5) / 0.3
        return 0.55 - t * 0.1
    t = (progress - 0.8) / 0.2
    return max(0.18, 0.30 - t * 0.12)


def _inside_irregular_boundary(x: int, y: int, size: int) -> bool:
    nx = (x - size * 0.5) / (size * 0.48)
    ny = (y - size * 0.52) / (size * 0.44)
    in_core = (nx * nx + ny * ny) <= 1.0
    notch = x < int(size * 0.18) and y < int(size * 0.32) and (x + y) < int(size * 0.24)
    return in_core and not notch


def _build_seed_grid(mean_ndvi: float, scan_date: date, farm_id: int) -> list[list[float | None]]:
    rng = random.Random(f"{farm_id}:{scan_date.isoformat()}")
    grid: list[list[float | None]] = []
    for y in range(GRID_SIZE):
        row: list[float | None] = []
        for x in range(GRID_SIZE):
            if not _inside_irregular_boundary(x, y, GRID_SIZE):
                row.append(None)
                continue
            stressed_corner = 0.18 if x < int(GRID_SIZE * 0.28) and y < int(GRID_SIZE * 0.28) else 0.0
            noise = rng.uniform(-0.06, 0.06)
            value = max(-0.10, min(0.95, mean_ndvi + noise - stressed_corner))
            row.append(round(value, 3))
        grid.append(row)
    return grid


def seed_demo_satellite_scans(
    db: Session,
    *,
    farm_id: int,
    season_start: date,
    season_end: date,
) -> None:
    dates = _date_range_every_five_days(season_start, season_end)
    if not dates:
        return
    total = max(1, len(dates) - 1)
    for idx, scan_date in enumerate(dates):
        progress = idx / total
        mean_ndvi = _mean_ndvi_for_progress(progress)
        ndvi_grid = _build_seed_grid(mean_ndvi, scan_date, farm_id)
        values = [v for row in ndvi_grid for v in row if v is not None]
        cloud_rng = random.Random(f"cloud:{farm_id}:{scan_date.isoformat()}")
        crud.upsert_satellite_scan(
            db,
            farm_id,
            {
                "scan_date": scan_date,
                "cloud_cover_pct": round(cloud_rng.uniform(1.5, 24.0), 2),
                "mean_ndvi": round(sum(values) / len(values), 3) if values else None,
                "max_ndvi": round(max(values), 3) if values else None,
                "min_ndvi": round(min(values), 3) if values else None,
                "ndvi_grid": ndvi_grid,
                # Synthetic grid drawn over the field; the frontend falls back
                # to the polygon bbox when bounds are null.
                "ndvi_grid_bounds": None,
                "source": "seed",
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo satellite NDVI history")
    parser.add_argument("--farm-id", type=int, required=True)
    parser.add_argument("--season-start", type=date.fromisoformat, required=True)
    parser.add_argument("--season-end", type=date.fromisoformat, required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        seed_demo_satellite_scans(
            db,
            farm_id=args.farm_id,
            season_start=args.season_start,
            season_end=args.season_end,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
