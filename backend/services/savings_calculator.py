"""Pure helpers: gallons saved → pump kWh saved → CO2 avoided, plus weekly periods.

All functions are deterministic with no I/O; the scheduler owns DB reads/writes.
"""
from datetime import date, timedelta
from decimal import Decimal

# Energy to lift 1 gallon by 1 foot: 8.34 lb/gal water weight over
# 2,655,224 ft·lb per kWh (1 kWh = 3.6e6 J, 1 ft·lb = 1.3558 J).
_KWH_PER_GALLON_FOOT = 8.34 / 2_655_224

# Overall pumping plant efficiency (motor x pump). 0.55 is the field average
# from PG&E's Advanced Pumping Efficiency Program / UC ANR pump test data for
# CA agricultural wells; per-pump efficiency capture is future onboarding work.
PUMP_PLANT_EFFICIENCY = 0.55

# CA grid carbon intensity: EPA eGRID2022, CAMX subregion, total output
# emission rate ~498 lb CO2/MWh = 0.226 kg CO2/kWh. https://www.epa.gov/egrid
CA_EGRID_KG_CO2_PER_KWH = 0.226


def gallons_to_kwh(gallons: Decimal, pump_lift_ft: Decimal | None) -> Decimal:
    """Pump energy to deliver `gallons` against `pump_lift_ft` of total head.

    Energy per gallon comes from lift and plant efficiency — pump horsepower is
    a power rating and cancels out of the per-gallon calculation. Farms without
    a recorded lift get 0 (no energy claim without pump data; conservative for
    grant reporting). Negative gallons (a week of overuse vs baseline) yield
    negative kWh — the sign is preserved so savings stay honest.
    """
    if pump_lift_ft is None:
        return Decimal("0.00")
    kwh = float(gallons) * float(pump_lift_ft) * _KWH_PER_GALLON_FOOT / PUMP_PLANT_EFFICIENCY
    return Decimal(str(round(kwh, 2)))


def kwh_to_co2_kg(kwh: Decimal) -> Decimal:
    return Decimal(str(round(float(kwh) * CA_EGRID_KG_CO2_PER_KWH, 2)))


def week_bounds(day: date) -> tuple[date, date]:
    """ISO week (Monday..Sunday) containing `day`."""
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)


def last_completed_week(today: date) -> tuple[date, date]:
    """Most recent Monday..Sunday week that ended strictly before `today`.

    Savings are only computed for completed weeks: a partial week's actual
    gallons compared against a full-week baseline would overstate savings.
    """
    return week_bounds(today - timedelta(days=7))
