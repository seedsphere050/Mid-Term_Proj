from datetime import datetime

def get_season():
    month = datetime.now().month

    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-Monsoon"


def get_rainfall(weather_data):
    if "rain" in weather_data:
        return weather_data["rain"].get("1h", 0) or weather_data["rain"].get("3h", 0)
    return 0


def rainfall_category(rainfall):
    if rainfall == 0:
        return "No Rain"
    elif rainfall < 10:
        return "Low"
    elif rainfall < 30:
        return "Moderate"
    else:
        return "Heavy"
