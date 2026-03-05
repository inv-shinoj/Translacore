import uuid
from django.db import models
from accounts.models import User
from project.models import Project
from .enums import DocumentStatus, FileType


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents",
    )

    original_filename = models.CharField(max_length=512)

    file_type = models.SmallIntegerField(
        choices=FileType.choices,
    )

    source_language = models.CharField(max_length=10, default="ja")
    target_language = models.CharField(max_length=10, default="en")

    source_s3_key = models.CharField(max_length=1024)
    translated_s3_key = models.CharField(max_length=1024, blank=True, default="")

    status = models.SmallIntegerField(
        choices=DocumentStatus.choices,
        default=DocumentStatus.UPLOADED,
    )

    error_message = models.TextField(blank=True, default="")

    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    page_count = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.get_status_display()})"


class TranslationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="translation_logs",
    )

    engine_used = models.CharField(max_length=100)
    char_count = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TranslationLog({self.document.original_filename}, {self.engine_used})"
