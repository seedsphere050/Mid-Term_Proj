# forget_pass/views.py
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PasswordResetOTP
from .serializers import EmailSerializer, OTPVerifySerializer, ResetPasswordSerializer

# -----------------------------
# 1️⃣ Send OTP
# -----------------------------
class SendOTPView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Delete old unverified OTPs
        PasswordResetOTP.objects.filter(user=user, is_verified=False).delete()

        # Create new OTP with timestamp
        PasswordResetOTP.objects.create(user=user, otp=otp, created_at=timezone.now())

        # Send OTP via email
        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP is {otp}",
            from_email="seedsphere050@gmail.com",  # replace with your email
            recipient_list=[email],
        )

        return Response({"message": "OTP sent successfully"}, status=200)


# -----------------------------
# 2️⃣ Verify OTP
# -----------------------------
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']

        # Get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Get latest unverified OTP
        otp_entry = PasswordResetOTP.objects.filter(user=user, is_verified=False).order_by('-id').first()

        if not otp_entry:
            return Response({"error": "Invalid OTP"}, status=400)

        # Check OTP match
        if str(otp_entry.otp) != str(otp_input):
            return Response({"error": "Invalid OTP"}, status=400)

        # Check expiration (optional, e.g., 10 minutes)
        if timezone.now() > otp_entry.created_at + timedelta(minutes=10):
            return Response({"error": "OTP expired"}, status=400)

        # Mark OTP as verified
        otp_entry.is_verified = True
        otp_entry.save()

        return Response({"message": "OTP verified successfully"}, status=200)


# -----------------------------
# 3️⃣ Reset Password
# -----------------------------
class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']
        new_password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Get the OTP that matches the input (verified or not)
        otp_entry = PasswordResetOTP.objects.filter(user=user, otp=otp_input).order_by('-id').first()

        if not otp_entry:
            return Response({"error": "Invalid OTP"}, status=400)

        # Check expiration
        from datetime import timedelta
        from django.utils import timezone

        if timezone.now() > otp_entry.created_at + timedelta(minutes=10):
            return Response({"error": "OTP expired"}, status=400)

        # Reset password
        user.set_password(new_password)
        user.save()

        # Mark OTP as verified (if not already)
        if not otp_entry.is_verified:
            otp_entry.is_verified = True
            otp_entry.save()

        return Response({"message": "Password reset successfully"})