from datetime import date
import math

def _compute_ra(latitude_deg: float, day_of_year: int) -> float:
    """Compute the extraterrestrial radiation (Ra) in MJ/m^2/day.

    Parameters
    ----------
    latitude_deg : float
        Latitude in degrees.
    day_of_year : int
        Day of the year (1-365).

    Returns
    -------
    float
        Extraterrestrial radiation (Ra) in MJ/m^2/day.
    """
    # Convert latitude to radians
    latitude_rad = math.radians(latitude_deg)

    # Solar declination (delta) in radians
    delta = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)

    # Sunset hour angle (omega_s) in radians
    omega_s = math.acos(-math.tan(latitude_rad) * math.tan(delta))

    # Relative distance Earth-Sun
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)  

    # Extraterrestrial radiation (Ra) in MJ/m^2/day
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        omega_s * math.sin(latitude_rad) * math.sin(delta) +
        math.cos(latitude_rad) * math.cos(delta) * math.sin(omega_s)
    )

    return ra


def _compute_et0_day(t_max_c: float, t_min_c: float, ra_mm: float) -> float:
    """Compute the reference evapotranspiration (ET0) for a single day.

    Parameters
    ----------
    t_max_c : float
        Maximum temperature in degrees Celsius.
    t_min_c : float
        Minimum temperature in degrees Celsius.
    ra_mm : float
        Extraterrestrial radiation (Ra) in mm/day.

    Returns
    -------
    float
        Reference evapotranspiration (ET0)
    """
    # Compute mean temperature
    t_mean_c = (t_max_c + t_min_c) / 2

    # Compute ET0 using the Hargreaves equation
    et0_mm = 0.0023 * (t_mean_c + 17.8) * math.sqrt(t_max_c - t_min_c) * ra_mm

    return et0_mm


def forecast_et0(forecast_days: list, latitude_deg: float) -> float:
    """Forecast reference evapotranspiration (ET0) for a list of forecast days.

    Parameters
    ----------
    forecast_days : list
        List of dictionaries containing 'date', 't_max_c', and 't_min_c' for each day.
    latitude_deg : float
        Latitude in degrees.

    Returns
    -------
    float
        Average daily ET0 in mm/day across all forecast days.
    """
    et0_values = []

    for day in forecast_days:
        date_str = day['date']
        t_max_c = day['t_max_c']
        t_min_c = day['t_min_c']

        # Convert date string to date object to get the day of the year
        date_obj = date.fromisoformat(date_str)
        day_of_year = date_obj.timetuple().tm_yday

        # Compute extraterrestrial radiation (Ra) in mm/day
        # Convert from MJ/m^2/day to mm/day using the latent heat of vaporization
        ra_mm = _compute_ra(latitude_deg, day_of_year) / 2.45

        # Compute ET0 for the day
        et0_mm = _compute_et0_day(t_max_c, t_min_c, ra_mm)

        et0_values.append(et0_mm)

    if not et0_values:
        return 0.0
    return sum(et0_values) / len(et0_values)

