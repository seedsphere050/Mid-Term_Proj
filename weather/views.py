from django.shortcuts import render
import requests
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.conf import settings
from .services import extract_weather_parameters
from .location import get_state_from_lat_lon
from .soil_data import get_soil_from_state

API_KEY = settings.API_KEY

class HelloAPI(APIView):
    def get(self, request):
        return Response({"message": "Backend is running successfully"})
#@authentication_classes([TokenAuthentication])
#@permission_classes([IsAuthenticated])
class WeatherAPI(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        lat = request.GET.get("lat")
        lon = request.GET.get("lon")

        if not lat or not lon:
            return Response(
                {"error": "Latitude and Longitude are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
        except Exception as e:
            return Response(
                {"error": "Failed to fetch weather data", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if "main" not in data:
            return Response(
                {"error": "Weather API error", "details": data},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        state = get_state_from_lat_lon(lat, lon)

# 2️⃣ Extract weather
        processed_weather = extract_weather_parameters(data, lat, lon)

# 3️⃣ Inject state manually
        processed_weather["state"] = state

# 4️⃣ Get soil
        soil_type = get_soil_from_state(state)
        processed_weather["soil_type"] = soil_type
        return Response({
            "location": {
                "city": data.get("name"),
                "state": state
            },
            "environment": processed_weather
        }, status=status.HTTP_200_OK)

    