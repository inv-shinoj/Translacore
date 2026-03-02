import uuid
from django.db import models
from accounts.models import User
from forms.models import FormSchema
from .enums import ProjectStatus


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)

    form_schema = models.ForeignKey(
        FormSchema,
        on_delete=models.PROTECT,
        related_name="projects"
    )

    project_data = models.JSONField()

    status = models.SmallIntegerField(
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    role = models.SmallIntegerField(
        choices=[
            (1, "Manager"),
            (2, "Lead"),
            (3, "Employee"),
        ]
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")
