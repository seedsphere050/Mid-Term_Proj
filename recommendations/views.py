from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .mongo import plants_collection
from weather.services import get_processed_weather_from_coords


# 🔥 Scoring Function
def score_plants(plants, weather):
    scored = []

    temp_data = weather.get("temperature", {})
    current_temp = temp_data.get("current")
    min_temp_weather = temp_data.get("min")
    max_temp_weather = temp_data.get("max")

    for plant in plants:
        env = plant.get("environment", {})
        score = 0

        # =========================
        # 1️⃣ TEMPERATURE (HIGH PRIORITY)
        # =========================
        env_temp = env.get("temperature", {})
        plant_min = env_temp.get("min")
        plant_max = env_temp.get("max")

        if plant_min is not None and plant_max is not None:
            match_count = 0

            if current_temp is not None and plant_min <= current_temp <= plant_max:
                match_count += 1

            if min_temp_weather is not None and plant_min <= min_temp_weather <= plant_max:
                match_count += 1

            if max_temp_weather is not None and plant_min <= max_temp_weather <= plant_max:
                match_count += 1

            score += match_count * 2   # HIGH weight

        # =========================
        # 2️⃣ SEASON
        # =========================
        if weather.get("season") in env.get("season", []):
            score += 2

        # =========================
        # 3️⃣ RAINFALL
        # =========================
        if weather.get("rainfall") == env.get("rainfall"):
            score += 2

        # =========================
        # 4️⃣ HUMIDITY
        # =========================
        if weather.get("humidity") == env.get("humidity"):
            score += 1

        # =========================
        # 5️⃣ SUNLIGHT
        # =========================
        if weather.get("sunlight") == env.get("sunlight"):
            score += 1

        # =========================
        # 6️⃣ SOIL TYPE
        # =========================
        if weather.get("soil_type") in env.get("soil_type", []):
            score += 1

        # Add only if some match
        if score > 0:
            scored.append((plant, score))

    # Sort by highest score
    scored.sort(key=lambda x: x[1], reverse=True)

    return [plant for plant, score in scored]


# 🚀 API View
class PlantRecommendationAPI(APIView):

    def get(self, request):
        try:
            lat = request.GET.get("lat")
            lon = request.GET.get("lon")

            if not lat or not lon:
                return Response(
                    {"error": "Latitude and Longitude are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 🌦️ Get weather data
            weather = get_processed_weather_from_coords(float(lat), float(lon))

            # 🌱 Fetch plants
            plants = list(plants_collection.find())

            if not plants:
                return Response(
                    {"recommended_plants": []},
                    status=status.HTTP_200_OK
                )

            # 🔥 Apply scoring
            scored_plants = score_plants(plants, weather)

            # =========================
            # 🎯 FALLBACK LOGIC
            # =========================
            if not scored_plants:
                # If no matches → return ANY 3 plants
                fallback = plants[:3]
                return Response(
                    {
                        "recommended_plants": [
                            {
                                "id": str(p.get("_id")),
                                "name": p.get("common_name"),
                                "scientific_name": p.get("scientific_name")
                            }
                            for p in fallback
                        ],
                        "message": "Fallback recommendations (low match)"
                    },
                    status=status.HTTP_200_OK
                )

            # 🔝 Top 3 best matches
            top_plants = scored_plants[:3]

            return Response(
                {
		    "weather_used": weather,
                    "recommended_plants": [
                        {
                            "id": str(p.get("_id")),
                            "name": p.get("common_name"),
                            "scientific_name": p.get("scientific_name")
                        }
                        for p in top_plants
                    ]
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )