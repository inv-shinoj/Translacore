import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import UserManager
from .enums import UserRole, AuthProvider


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)

    role = models.SmallIntegerField(
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE
    )

    auth_provider = models.SmallIntegerField(
        choices=AuthProvider.choices
    )

    google_sub = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
