from django.shortcuts import render
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import get_recommended_plants


class PlantRecommendationAPI(APIView):
    """
    Recommends plants dynamically from MongoDB
    based on climate zone ID, plant type, and maintenance level.
    """

    def post(self, request):
        # Read user inputs from frontend
        climate_zone_id = request.data.get("climate_zone_id")
        plant_type = request.data.get("plant_type")            # string
        maintenance_level = request.data.get("maintenance_level")  # string

        # Validate required fields
        if not climate_zone_id:
            return Response(
                {"error": "climate_zone_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Call service layer (business logic)
        plants = get_recommended_plants(
            climate_zone_id=climate_zone_id,
            plant_type=plant_type,
            maintenance_level=maintenance_level
        )

        # Return dynamic response
        return Response({
            "filters_used": {
                "climate_zone_id": climate_zone_id,
                "plant_type": plant_type,
                "maintenance_level": maintenance_level
            },
            "total_recommendations": len(plants),
            "recommended_plants": plants
        }, status=status.HTTP_200_OK)

# class PlantRecommendationAPI(APIView):
#     def get(self, request):
#         lat = request.GET.get("lat")
#         lon = request.GET.get("lon")

#         if not lat or not lon:
#             return Response({"error": "lat & lon required"}, status=400)

#         weather_url = "https://api.openweathermap.org/data/2.5/weather"
#         params = {
#             "lat": lat,
#             "lon": lon,
#             "appid": settings.API_KEY,
#             "units": "metric"
#         }

#         weather = requests.get(weather_url, params=params).json()

#         temp = weather["main"]["temp"]
#         humidity = weather["main"]["humidity"]
#         condition = weather["weather"][0]["main"].lower()

#         plants = get_recommended_plants(temp, humidity, condition)

#         return Response({
#             "location": weather["name"],
#             "weather": {
#                 "temperature": temp,
#                 "humidity": humidity,
#                 "condition": condition
#             },
#             "recommended_plants": plants
#         })

# # Create your views here.


