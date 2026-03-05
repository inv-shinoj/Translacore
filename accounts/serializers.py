from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import User
from .enums import AuthProvider, UserRole


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "full_name", "email", "role", "is_active")


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()

from rest_framework import serializers

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "full_name", "password")

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists"
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(
            **validated_data,
            role=UserRole.EMPLOYEE,
            auth_provider=AuthProvider.PASSWORD
        )
        user.set_password(password)
        user.save()

        return user


class CreateUserAdminSerializer(serializers.ModelSerializer):
    """Admin creates a user with an explicit role."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "full_name", "password", "role")

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists"
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data, auth_provider=AuthProvider.PASSWORD)
        user.set_password(password)
        user.save()
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    """Admin can update full_name, role, and is_active."""

    class Meta:
        model = User
        fields = ("full_name", "role", "is_active")

    def validate_role(self, value):
        valid = [choice[0] for choice in UserRole.choices]
        if value not in valid:
            raise serializers.ValidationError("Invalid role.")
        return value
