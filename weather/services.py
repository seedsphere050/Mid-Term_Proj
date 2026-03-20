import requests
from django.conf import settings
from .soil_data import STATE_SOIL_MAP
from datetime import datetime

API_KEY = settings.API_KEY

def get_state_from_lat_lon(lat, lon):
    url = "https://api.openweathermap.org/geo/1.0/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "limit": 1,
        "appid": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if not data:
        return None

    return data[0].get("state")

def get_season():
    month = datetime.now().month

    if month in [12, 1]:
        return "Winter"
    elif month in [2, 3]:
        return "Spring"
    elif month in [4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-Monsoon"


def extract_weather_parameters(data,lat,lon):
    # 🌡️ Temperature
    temp_current = data["main"].get("temp")
    temp_min = data["main"].get("temp_min")
    temp_max = data["main"].get("temp_max")

    # 💧 Humidity (numeric)
    humidity_value = data["main"].get("humidity")

    # 🌧️ Rainfall (numeric)
    rainfall_value = 0
    if "rain" in data:
        rainfall_value = data["rain"].get("1h", data["rain"].get("3h", 0))

    # 🔄 Rainfall category
    if rainfall_value == 0:
        rainfall = "Low"
    elif rainfall_value < 5:
        rainfall = "Moderate"
    else:
        rainfall = "Heavy"

    # 🔄 Humidity category
    if humidity_value < 40:
        humidity = "Low"
    elif humidity_value < 70:
        humidity = "Medium"
    else:
        humidity = "High"

    # ☀️ Sunlight (based on cloud percentage)
    clouds = data.get("clouds", {}).get("all", 0)
    if clouds < 30:
        sunlight = "Full Sun"
    elif clouds < 70:
        sunlight = "Partial Sun"
    else:
        sunlight = "Low Sunlight"

    # 🌦️ Season (derived)
    season = get_season()

    return {
        "temperature": {
            "current": temp_current,
            "min": temp_min,
            "max": temp_max
        },
        "season": season,
        "humidity": humidity,
        "rainfall": rainfall,
        "sunlight": sunlight,
    }

def get_processed_weather_from_coords(lat, lon):
    """
    Fetch raw weather from OpenWeather API
    and return processed weather parameters
    """

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code != 200:
        return None

    processed_weather = extract_weather_parameters(data, lat, lon)

    # 🌱 Add soil info
    state = get_state_from_lat_lon(lat, lon)
    soil_type = STATE_SOIL_MAP.get(state, [])

    processed_weather["soil_type"] = soil_type
    processed_weather["state"] = state

    return processed_weather
