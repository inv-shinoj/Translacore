import uuid
from django.db import models
from accounts.models import User
from .enums import FormTypeKey, SchemaStatus


class FormType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    key = models.SmallIntegerField(
        choices=FormTypeKey.choices,
        unique=True
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_key_display()


class FormSchema(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    form_type = models.ForeignKey(
        FormType,
        on_delete=models.CASCADE,
        related_name="schemas"
    )

    name = models.CharField(max_length=150)
    schema_json = models.JSONField()

    version = models.PositiveIntegerField()

    status = models.SmallIntegerField(
        choices=SchemaStatus.choices,
        default=SchemaStatus.INACTIVE
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("form_type", "version")
        ordering = ["-version"]

    def __str__(self):
        return f"{self.form_type.get_key_display()} v{self.version}"
