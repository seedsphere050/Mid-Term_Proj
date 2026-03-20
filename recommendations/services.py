from .models import Plant

def recommend_plants(weather_data):
    temp = weather_data["temperature"]["current"]
    season = weather_data["season"]
    rainfall = weather_data["rainfall"]
    humidity = weather_data["humidity"]
    sunlight = weather_data["sunlight"]

    plants = Plant.objects.all()
    recommended = []

    for plant in plants:
        # 1️⃣ Temperature check
        if not (plant.min_temp <= temp <= plant.max_temp):
            continue

        # 2️⃣ Season check
        if season not in plant.season:
            continue

        # 3️⃣ Rainfall check
        if rainfall not in plant.rainfall:
            continue

        # 4️⃣ Humidity check
        if humidity not in plant.humidity:
            continue

        # 5️⃣ Sunlight check
        if sunlight not in plant.sunlight:
            continue

        recommended.append(plant.name)

    return recommended