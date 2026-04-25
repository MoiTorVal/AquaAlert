from dotenv import load_dotenv
from datetime import datetime
from backend.database import SessionLocal
from backend.crud import create_weather_reading
from backend.schemas import WeatherReadingCreate
from backend.config import settings
import requests
import logging

logger = logging.getLogger(__name__)


def get_weather_data(location):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={settings.openweather_api_key.get_secret_value()}&units=metric"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching weather data: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return None
    
def parse_weather_data(data):
    if data is None:
        return None
    
    try:
        temperature_c = data["main"]["temp"]
        humidity_pct = data["main"]["humidity"]
        weather_description = data["weather"][0]["description"]
        rainfall_mm = data["rain"]["1h"] if "rain" in data and "1h" in data["rain"] else 0
        wind_speed_kph = data["wind"]["speed"] * 3.6 if "wind" in data and "speed" in data["wind"] else 0
        location = data["name"]
        recorded_at = datetime.fromtimestamp(data["dt"])
        return {
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "description": weather_description,
            "rainfall_mm": rainfall_mm,
            "wind_speed_kph": wind_speed_kph,
            "location": location,
            "recorded_at": recorded_at
        }
    except (KeyError, TypeError) as e:
        logger.error(f"Error parsing weather data: {e}")
        return None

def fetch_and_save_weather_data(location, farm_id):
    db = SessionLocal()
    try:
        weather_data = get_weather_data(location)
        parsed_data = parse_weather_data(weather_data)
        if parsed_data:
            parsed_data["farm_id"] = farm_id
            result = create_weather_reading(db, WeatherReadingCreate(**parsed_data))
            return result
        return None
    finally:
        db.close()


if __name__ == "__main__":
    result = fetch_and_save_weather_data("Fresno", 1)
    print(result)