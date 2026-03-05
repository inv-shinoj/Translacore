import os

from rest_framework import serializers
from .models import Document
from .enums import ALLOWED_EXTENSIONS, FILE_EXTENSION_MAP, MAX_FILE_SIZE
from . import storage


class DocumentUploadSerializer(serializers.Serializer):
    """Accepts a file upload; validates type and size."""

    file = serializers.FileField()

    def validate_file(self, file):
        # Check extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Check size
        if file.size > MAX_FILE_SIZE:
            mb = MAX_FILE_SIZE // (1024 * 1024)
            raise serializers.ValidationError(
                f"File too large ({file.size:,} bytes). Maximum is {mb} MB."
            )

        return file


class DocumentListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    file_type_display = serializers.CharField(source="get_file_type_display", read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True, default="")

    class Meta:
        model = Document
        fields = (
            "id",
            "original_filename",
            "file_type",
            "file_type_display",
            "source_language",
            "target_language",
            "status",
            "status_display",
            "file_size",
            "page_count",
            "uploaded_by_name",
            "created_at",
            "updated_at",
        )


class DocumentDetailSerializer(DocumentListSerializer):
    """Extends list serializer with presigned download URLs."""

    source_download_url = serializers.SerializerMethodField()
    translated_download_url = serializers.SerializerMethodField()

    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + (
            "error_message",
            "source_download_url",
            "translated_download_url",
        )

    def get_source_download_url(self, obj):
        if obj.source_s3_key:
            try:
                return storage.generate_presigned_url(obj.source_s3_key)
            except Exception:
                return None
        return None

    def get_translated_download_url(self, obj):
        if obj.translated_s3_key:
            try:
                return storage.generate_presigned_url(obj.translated_s3_key)
            except Exception:
                return None
        return None
