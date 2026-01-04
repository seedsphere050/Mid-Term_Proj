from django.urls import path
from .views import HelloAPI, WeatherAPI

urlpatterns = [
    path('hello/', HelloAPI.as_view()),
    path('', WeatherAPI.as_view()),
]
