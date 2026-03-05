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
    LogoutSerializer,
    UserListSerializer,
    CreateUserAdminSerializer,
    UpdateUserSerializer,
)
from .utils.jwt import generate_tokens
from .utils.google import verify_google_token
from .enums import AuthProvider, UserRole


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
        except Exception as e:
            print(f"[GoogleLogin] Token verification failed: {e}")
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


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if request.user.role != UserRole.ADMIN:
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

    def get(self, request):
        if request.user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            return Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )
        users = User.objects.exclude(id=request.user.id)
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        err = self._require_admin(request)
        if err:
            return err

        serializer = CreateUserAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserListSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        if request.user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        user = self._get_user(pk)
        if not user:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserListSerializer(user).data)

    def patch(self, request, pk):
        if request.user.role != UserRole.ADMIN:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        user = self._get_user(pk)
        if not user:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user.refresh_from_db()
        return Response(UserListSerializer(user).data)

    def delete(self, request, pk):
        if request.user.role != UserRole.ADMIN:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        user = self._get_user(pk)
        if not user:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if str(user.id) == str(request.user.id):
            return Response({"detail": "Cannot deactivate yourself."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
