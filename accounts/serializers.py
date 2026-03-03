from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import User
from .enums import AuthProvider, UserRole


class UserListSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "full_name", "email", "role", "role_display")


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
