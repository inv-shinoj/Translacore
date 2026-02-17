from django.db import models


class FormTypeKey(models.IntegerChoices):
    PROJECT = 1, "Project"
    LEGAL = 2, "Legal"
    TECH = 3, "Technical"
    FINANCE = 4, "Finance"


class SchemaStatus(models.IntegerChoices):
    INACTIVE = 0, "Inactive"
    ACTIVE = 1, "Active"
