import csv
import io
from datetime import date
from decimal import Decimal

import pytest

from backend import crud, models
from backend.enums import JobStatus, StressSeverity
from backend.schemas import (
    AquaCropOutputBase,
    FarmCreate,
    IrrigationEventCreate,
    WaterSavingsBase,
)
from backend.services.scheduler import REGIONAL_STATS_JOB_NAME, run_regional_stats_job

WEEK1 = (date(2026, 5, 25), date(2026, 5, 31))
WEEK2 = (date(2026, 6, 1), date(2026, 6, 7))


def _savings_row(db, farm_id, period, gallons_saved="3000.00", kwh="1.71", co2="0.39"):
    return crud.upsert_water_savings(db, farm_id, WaterSavingsBase(
        period_start=period[0],
        period_end=period[1],
        baseline_gallons=Decimal("7000.00"),
        actual_gallons=Decimal("7000.00") - Decimal(gallons_saved),
        gallons_saved=Decimal(gallons_saved),
        kwh_saved=Decimal(kwh),
        co2_kg_saved=Decimal(co2),
    ))


# ── GET /farms/{id}/savings ──────────────────────────────────────────────────


def test_savings_series_returns_rows_and_totals(client, db, farm):
    _savings_row(db, farm.id, WEEK1)
    _savings_row(db, farm.id, WEEK2, gallons_saved="2000.00", kwh="1.14", co2="0.26")

    response = client.get(f"/farms/{farm.id}/savings?from=2026-05-25&to=2026-06-07")
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    assert body["totals"]["gallons_saved"] == "5000.00"
    assert body["totals"]["kwh_saved"] == "2.85"
    assert body["totals"]["baseline_gallons"] == "14000.00"


def test_savings_series_filters_range(client, db, farm):
    _savings_row(db, farm.id, WEEK1)
    _savings_row(db, farm.id, WEEK2)
    response = client.get(f"/farms/{farm.id}/savings?from=2026-06-01&to=2026-06-07")
    body = response.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["period_start"] == "2026-06-01"


def test_savings_series_rejects_inverted_range(client, farm):
    response = client.get(f"/farms/{farm.id}/savings?from=2026-06-07&to=2026-06-01")
    assert response.status_code == 422


def test_savings_series_unknown_farm(client):
    response = client.get("/farms/9999/savings?from=2026-06-01&to=2026-06-07")
    assert response.status_code == 404


def test_savings_series_unauthenticated(unauthed_client, farm):
    response = unauthed_client.get(f"/farms/{farm.id}/savings?from=2026-06-01&to=2026-06-07")
    assert response.status_code == 401


# ── GET /farms/{id}/sgma-export ──────────────────────────────────────────────


def _log_events(db, farm_id):
    crud.create_irrigation_event(db, farm_id, IrrigationEventCreate(
        event_date=date(2026, 6, 2), gallons_applied=Decimal("325851")))  # 1 acre-foot
    crud.create_irrigation_event(db, farm_id, IrrigationEventCreate(
        event_date=date(2026, 6, 20), gallons_applied=Decimal("100000")))
    crud.create_irrigation_event(db, farm_id, IrrigationEventCreate(
        event_date=date(2026, 7, 4), gallons_applied=Decimal("50000")))


def test_sgma_csv_contains_monthly_totals(client, db, farm):
    _log_events(db, farm.id)
    response = client.get(f"/farms/{farm.id}/sgma-export?year=2026&format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="sgma-report-2026-farm-' in response.headers["content-disposition"]
    text = response.text
    assert "June,425851.00," in text
    assert "July,50000.00," in text
    assert "TOTAL,475851.00," in text
    assert "January,0,0.0000" in text  # all 12 months present


def test_sgma_csv_excludes_other_years(client, db, farm):
    crud.create_irrigation_event(db, farm.id, IrrigationEventCreate(
        event_date=date(2025, 6, 2), gallons_applied=Decimal("99999")))
    response = client.get(f"/farms/{farm.id}/sgma-export?year=2026&format=csv")
    assert "99999" not in response.text


def test_sgma_pdf_returns_pdf(client, db, farm):
    _log_events(db, farm.id)
    response = client.get(f"/farms/{farm.id}/sgma-export?year=2026&format=pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_sgma_rejects_bad_format(client, farm):
    response = client.get(f"/farms/{farm.id}/sgma-export?year=2026&format=xlsx")
    assert response.status_code == 422


def test_sgma_unauthenticated(unauthed_client, farm):
    response = unauthed_client.get(f"/farms/{farm.id}/sgma-export?year=2026")
    assert response.status_code == 401


def test_sgma_csv_neutralizes_formula_injection(client, db):
    # The export is opened by GSA staff in Excel — a farm name must never
    # become an executable formula (CWE-1236) or inject CSV rows.
    create = client.post(
        "/farms/", json={"name": '=HYPERLINK("http://evil",1)\nTOTAL,999,999'}
    )
    assert create.status_code == 201
    farm_id = create.json()["id"]
    _log_events(db, farm_id)

    response = client.get(f"/farms/{farm_id}/sgma-export?year=2026&format=csv")
    assert response.status_code == 200
    text = response.text
    assert "'=HYPERLINK" in text  # formula char defused with apostrophe
    for row in csv.reader(io.StringIO(text)):
        for cell in row:
            assert not cell.startswith(("=", "+", "@"))
    # real totals row still intact despite the injected "TOTAL" line
    assert "TOTAL,475851.00," in text


def test_sgma_pdf_escapes_markup_in_farm_name(client, db):
    # reportlab Paragraph parses XML-ish tags; unescaped user text crashes
    # the build (500) on malformed markup.
    create = client.post("/farms/", json={"name": "Farm <foo> & Sons"})
    assert create.status_code == 201
    farm_id = create.json()["id"]
    _log_events(db, farm_id)

    response = client.get(f"/farms/{farm_id}/sgma-export?year=2026&format=pdf")
    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


# ── regional stats job + public endpoint ─────────────────────────────────────


def _farm_with_severity(db, user_id, name, severity, as_of=date(2026, 6, 8)):
    farm = crud.create_farm(db, FarmCreate(name=name), user_id=user_id)
    crud.upsert_aquacrop_output(db, farm.id, AquaCropOutputBase(
        as_of_date=as_of,
        depletion_mm=Decimal("30.00"),
        root_zone_moisture_pct=Decimal("70.00"),
        severity=severity,
        days_to_stress=10,
        paw_mm=Decimal("80.00"),
        raw_threshold_mm=Decimal("76.00"),
    ))
    return farm


def test_count_farms_by_severity_uses_latest_output(db, user):
    farm = _farm_with_severity(db, user.id, "F1", StressSeverity.GREEN, as_of=date(2026, 6, 1))
    # newer output flips it to red — only the latest should count
    crud.upsert_aquacrop_output(db, farm.id, AquaCropOutputBase(
        as_of_date=date(2026, 6, 8),
        depletion_mm=Decimal("80.00"),
        root_zone_moisture_pct=Decimal("20.00"),
        severity=StressSeverity.RED,
        days_to_stress=0,
        paw_mm=Decimal("20.00"),
        raw_threshold_mm=Decimal("76.00"),
    ))
    counts = crud.count_farms_by_severity(db)
    assert counts == {"green": 0, "yellow": 0, "red": 1}


def test_regional_stats_job_aggregates(db, user):
    _farm_with_severity(db, user.id, "G", StressSeverity.GREEN)
    _farm_with_severity(db, user.id, "Y", StressSeverity.YELLOW)
    red_farm = _farm_with_severity(db, user.id, "R", StressSeverity.RED)
    _savings_row(db, red_farm.id, WEEK2)

    job_run = run_regional_stats_job(db=db, today=date(2026, 6, 9))
    assert job_run.job_name == REGIONAL_STATS_JOB_NAME
    assert job_run.status == JobStatus.SUCCESS

    stats = crud.get_latest_regional_stats(db)
    assert stats.total_farms == 3
    assert (stats.farms_green, stats.farms_yellow, stats.farms_red) == (1, 1, 1)
    assert stats.total_gallons_saved == Decimal("3000.00")


def test_regional_stats_job_upsert_idempotent(db, user):
    _farm_with_severity(db, user.id, "G", StressSeverity.GREEN)
    run_regional_stats_job(db=db, today=date(2026, 6, 9))
    run_regional_stats_job(db=db, today=date(2026, 6, 9))
    assert db.query(models.RegionalStats).count() == 1


def test_impact_stats_public_no_auth_required(unauthed_client, db, user):
    for name in ("A", "B", "C"):
        _farm_with_severity(db, user.id, name, StressSeverity.GREEN)
    run_regional_stats_job(db=db, today=date(2026, 6, 9))

    response = unauthed_client.get("/impact/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_farms"] == 3
    assert body["farms_green"] == 3
    # anonymization: aggregates only, nothing farm-identifiable or equity-related
    assert "results" not in body
    for forbidden in ("name", "is_socially_disadvantaged", "is_beginning_farmer"):
        assert forbidden not in body


def test_impact_stats_suppressed_below_min_cohort(unauthed_client, db, user):
    _farm_with_severity(db, user.id, "Lonely", StressSeverity.GREEN)
    run_regional_stats_job(db=db, today=date(2026, 6, 9))
    response = unauthed_client.get("/impact/stats")
    assert response.status_code == 404


def test_impact_stats_no_snapshot_404(unauthed_client):
    response = unauthed_client.get("/impact/stats")
    assert response.status_code == 404
