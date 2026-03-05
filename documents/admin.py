from django.contrib import admin
from .models import Document, TranslationLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "project", "status", "file_type", "uploaded_by", "created_at")
    list_filter = ("status", "file_type")
    search_fields = ("original_filename",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TranslationLog)
class TranslationLogAdmin(admin.ModelAdmin):
    list_display = ("document", "engine_used", "char_count", "duration_ms", "created_at")
    readonly_fields = ("id", "created_at")
