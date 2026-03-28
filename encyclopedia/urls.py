from django.urls import path
from .views import PlantsAPIView

urlpatterns = [
    path('plants/', PlantsAPIView.as_view()),  # matches your frontend fetch("/api/plants")
]