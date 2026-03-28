from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from accounts.mongo import users_collection

class RegisterAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        password = request.data.get("password")
        confirm_password = request.data.get("confirmPassword")
        phone = request.data.get("phone")

        # 🔹 Validate fields
        if not name or not email or not password or not confirm_password or not phone:
            return Response(
                {"error": "All fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Password match
        if password != confirm_password:
            return Response(
                {"error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Check duplicate in Django
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Check duplicate in MongoDB
        if users_collection.find_one({"email": email}):
            return Response(
                {"error": "User already exists in MongoDB"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # ✅ IMPORTANT: use email as username
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            print("✅ Django user created")

            # ✅ Save in MongoDB
            result = users_collection.insert_one({
                "django_user_id": user.id,
                "name": name,
                "email": email,
                "phone": phone
            })

            print("✅ Mongo inserted:", result.inserted_id)

            return Response(
                {
                    "message": "User registered successfully",
                    "email": email
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print("❌ ERROR:", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
from rest_framework.authtoken.models import Token

class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # 🔹 Validate input
        if not email or not password:
            return Response(
                {"error": "Email and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Authenticate using email as username
        user = authenticate(username=email, password=password)
        if user:
            print("Login successful:)")
        if not user:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ✅ Generate token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "email": user.email
        })