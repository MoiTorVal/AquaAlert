from typing import Optional
from .water_balance import _get_kc

def estimate_soil_moisture(farm, weather_readings, initial_moisture_pct=None):
    fc = float(farm.field_capacity or 30.0)
    wp = float(farm.wilting_point or 15.0)
    crop = (farm.crop_type or "default").strip().lower()
    stage = (farm.growth_stage or "mid").strip().lower()

    kc = _get_kc(crop, stage)

    moisture = initial_moisture_pct if initial_moisture_pct is not None else fc

    for reading in weather_readings: 
        et0 = float(reading.et0.mm or 0.0)
        rain = float(reading.rainfall_mm or 0.0)

        etc = et0 * kc
        moisture = moisture - (etc / (fc - wp) * 100) + (rain / (fc - wp) * 100)
        moisture = max(wp, min(moisture, fc))

    return round(moisture, 2)    

