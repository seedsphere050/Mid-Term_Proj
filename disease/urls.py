# # disease/urls.py
# from django.urls import path
# from .views import DetectDiseaseAPI, DiseasesAPI, DiseaseDetailAPI

# urlpatterns = [
#     path("detect/", DetectDiseaseAPI.as_view(), name="detect_disease"),
#     path("diseases/", DiseasesAPI.as_view(), name="get_diseases"),
#     path("diseases/<str:disease_name>/", DiseaseDetailAPI.as_view(), name="get_disease_detail"),
# ]

# disease/urls.py
from django.urls import path
from .views import detect_disease, get_diseases, get_disease_detail

urlpatterns = [
    path("detect/", detect_disease, name="detect_disease"),
    path("diseases/", get_diseases, name="get_diseases"),
    path("diseases/<str:disease_name>/", get_disease_detail, name="get_disease_detail"),
]