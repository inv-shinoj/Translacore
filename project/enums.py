from django.db import models


class ProjectStatus(models.IntegerChoices):
    DRAFT = 1, "Draft"
    ACTIVE = 2, "Active"
    COMPLETED = 3, "Completed"
    ARCHIVED = 4, "Archived"
