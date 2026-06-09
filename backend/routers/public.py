"""Public, unauthenticated endpoints for the /impact dashboard.

Serves only pre-aggregated RegionalStats snapshots (computed nightly by the
scheduler) — never live per-farm queries, never equity fields. Aggregates are
suppressed below MIN_COHORT_SIZE farms so no individual farm is inferable.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import crud
from backend.database import get_db
from backend.schemas import RegionalStatsResponse

router = APIRouter()

MIN_COHORT_SIZE = 3


@router.get("/impact/stats", response_model=RegionalStatsResponse)
def get_impact_stats(db: Session = Depends(get_db)):
    stats = crud.get_latest_regional_stats(db=db)
    if stats is None or stats.total_farms < MIN_COHORT_SIZE:
        raise HTTPException(
            status_code=404,
            detail="Not enough participating farms to publish aggregates yet",
        )
    return stats
