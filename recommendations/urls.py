from django.urls import path
from .views import PlantRecommendationAPI

urlpatterns = [
    path('plants/', PlantRecommendationAPI.as_view(), name='plant-recommendation'),
]
