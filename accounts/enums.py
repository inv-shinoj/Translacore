from django.db import models

class UserRole(models.IntegerChoices):
    ADMIN = 1, "Admin"
    MANAGER = 2, "Manager"
    LEAD = 3, "Team Lead"
    EMPLOYEE = 4, "Employee"


class AuthProvider(models.IntegerChoices):
    GOOGLE = 1, "Google"
    PASSWORD = 2, "Password"
