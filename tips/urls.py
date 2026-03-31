from django.urls import path
from .views import random_tip

urlpatterns = [
    path('random/', random_tip),
]