from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from weather.services import get_processed_weather_from_coords
from .models import Plant


# ✅ helper function (outside class)
def refine(plants, field, value):
    result = []

    for plant in plants:
        plant_value = getattr(plant, field, None)

        if plant_value is None:
            continue

        if isinstance(plant_value, (list, tuple)):
            if value in plant_value:
                result.append(plant)

        elif isinstance(plant_value, dict):
            if value in plant_value.values():
                result.append(plant)

        else:
            if plant_value == value:
                result.append(plant)

    return result if result else plants


class PlantRecommendationAPI(APIView):

    def get(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            return Response(
                {"error": "lat and lon are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        weather = get_processed_weather_from_coords(float(lat), float(lon))

        if not weather:
            return Response(
                {"error": "Unable to fetch weather data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        plants = list(Plant.objects.all())

        plants = refine(plants, "season", weather["season"])
        plants = refine(plants, "rainfall", weather["rainfall"])
        plants = refine(plants, "humidity", weather["humidity"])
        plants = refine(plants, "sunlight", weather["sunlight"])

        # ✅ minimal response (you can add serializer later)
        data = [
            {
                "id": plant.id,
                "name": plant.name,
                "season": plant.season,
                "sunlight": plant.sunlight,
            }
            for plant in plants
        ]

        return Response(
            {
                "weather_used": weather,
                "recommended_plants": data
            },
            status=status.HTTP_200_OK
        )