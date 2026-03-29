from django.urls import path
from .views import (
    PlantListCreateView,
    PlantDetailView,
    PlantWaterView,
    WeatherView,
    PlantCareLogsView,
    PlantFertilizeView,
)

urlpatterns = [
    # Plants
    path('', PlantListCreateView.as_view()),
    path('<str:plant_id>/', PlantDetailView.as_view()),
    path('<str:plant_id>/care-logs/', PlantCareLogsView.as_view()),

    # Water
    path('<str:plant_id>/water/', PlantWaterView.as_view()),
    path('<str:plant_id>/fertilize/', PlantFertilizeView.as_view()),
    # Weather
    path('weather/', WeatherView.as_view()),
]