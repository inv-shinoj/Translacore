from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

from .serializers import (
    EmailLoginSerializer, 
    GoogleLoginSerializer, 
    RegisterSerializer,
    LogoutSerializer)
from .utils.jwt import generate_tokens
from .utils.google import verify_google_token
from .enums import AuthProvider


class EmailLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.auth_provider != AuthProvider.PASSWORD:
            return Response(
                {"detail": "Use Google login"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tokens = generate_tokens(user)

        return Response({
            **tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.get_role_display(),
            }
        })


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = verify_google_token(serializer.validated_data["id_token"])
        except Exception:
            return Response(
                {"detail": "Invalid Google token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        google_sub = payload["sub"]
        email = payload["email"]
        name = payload.get("name", "")

        user, created = User.objects.get_or_create(
            google_sub=google_sub,
            defaults={
                "email": email,
                "full_name": name,
                "auth_provider": AuthProvider.GOOGLE,
            }
        )

        if not created and user.auth_provider != AuthProvider.GOOGLE:
            return Response(
                {"detail": "Use email/password login"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tokens = generate_tokens(user)

        return Response({
            **tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.get_role_display(),
            }
        })
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Logged out successfully"},
            status=status.HTTP_205_RESET_CONTENT
        )
    
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        tokens = generate_tokens(user)

        return Response(
            {
                **tokens,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.get_role_display(),
                }
            },
            status=status.HTTP_201_CREATED
        )
    