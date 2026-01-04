from django.shortcuts import render
import requests
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
API_KEY = "7db07d71134b6c830342a867f6b5c793"

class HelloAPI(APIView):
    def get(self, request):
        return Response({"message": "Backend is running successfully"})
#@authentication_classes([TokenAuthentication])
#@permission_classes([IsAuthenticated])
class WeatherAPI(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        lat = request.GET.get("lat")
        lon = request.GET.get("lon")

        if not lat or not lon:
            return Response(
                {"error": "Latitude and Longitude are required"},
                status=400
            )

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "main" not in data:
            return Response(
                {"error": "Weather API error", "details": data},
                status=500
            )

        return Response({
            "city": data.get("name"),
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "weather": data["weather"][0]["description"]
        })

