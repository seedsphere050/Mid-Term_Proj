"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('weather.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api-auth/', include('rest_framework.urls')), 
    path('api/recommend/', include('recommendations.urls')),
    path("api/", include("encyclopedia.urls")),
    path('api/forget-pass/', include('forget_pass.urls')),
    path("api/", include("disease.urls")),
    path('api/care/', include('care_reminders.urls')),
    path('api/twin/', include('twin.urls')),
    path('api/tips/', include('tips.urls')),

 # <- This enables login in DRF UI
]


