import requests
from django.conf import settings

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
