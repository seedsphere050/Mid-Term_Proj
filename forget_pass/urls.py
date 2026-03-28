# forget_pass/urls.py
from django.urls import path
from .views import SendOTPView, VerifyOTPView, ResetPasswordView

urlpatterns = [
    path('send-otp/', SendOTPView.as_view()),
    path('verify-otp/', VerifyOTPView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
]