# ============================================================
# CHANGE: NEW FILE — care_reminders/services/weather.py
# Fetches live weather from OpenWeatherMap and maps it to
# one of 5 conditions used for watering schedule adjustment.
# ============================================================
import os
import requests

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')

# How much weather multiplies the base watering interval
# sunny/hot = water sooner (multiplier < 1), rainy/cold = delay
WEATHER_MULTIPLIERS = {
    'sunny':  0.70,
    'cloudy': 1.00,
    'rainy':  1.50,
    'hot':    0.60,
    'cold':   1.40,
}


def fetch_weather(location: str) -> dict:
    """
    Fetch weather for city name or 'lat,lon'.
    Returns: {'condition': str, 'temp_c': float, 'humidity': int}
    Falls back to 'cloudy' on any error or missing API key.
    """
    if not location or not OPENWEATHER_API_KEY:
        return {'condition': 'cloudy', 'temp_c': 25, 'humidity': 60}
    try:
        if ',' in location and all(p.strip().replace('.','').replace('-','').isdigit()
                                    for p in location.split(',')):
            lat, lon = location.split(',')
            url = (f'https://api.openweathermap.org/data/2.5/weather'
                   f'?lat={lat.strip()}&lon={lon.strip()}&appid={OPENWEATHER_API_KEY}&units=metric')
        else:
            url = (f'https://api.openweathermap.org/data/2.5/weather'
                   f'?q={location}&appid={OPENWEATHER_API_KEY}&units=metric')
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        temp     = data['main']['temp']
        humidity = data['main']['humidity']
        main     = data['weather'][0]['main'].lower()
        if 'rain' in main or 'drizzle' in main:
            condition = 'rainy'
        elif 'clear' in main and temp > 35:
            condition = 'hot'
        elif 'clear' in main:
            condition = 'sunny'
        elif temp < 15:
            condition = 'cold'
        else:
            condition = 'cloudy'
        return {'condition': condition, 'temp_c': round(temp, 1), 'humidity': humidity}
    except Exception:
        return {'condition': 'cloudy', 'temp_c': 25, 'humidity': 60}


def calc_adjusted_days(base_days: int, condition: str) -> int:
    """Multiply base interval by weather multiplier, minimum 1 day."""
    mult = WEATHER_MULTIPLIERS.get(condition, 1.0)
    return max(1, round(base_days * mult))
