from django.db import models


class DocumentStatus(models.IntegerChoices):
    UPLOADED = 1, "Uploaded"
    TRANSLATING = 2, "Translating"
    COMPLETED = 3, "Completed"
    FAILED = 4, "Failed"


class FileType(models.IntegerChoices):
    TXT = 1, "txt"
    PDF = 2, "pdf"
    DOCX = 3, "docx"
    XLSX = 4, "xlsx"


FILE_EXTENSION_MAP = {
    ".txt": FileType.TXT,
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".xlsx": FileType.XLSX,
}

ALLOWED_EXTENSIONS = set(FILE_EXTENSION_MAP.keys())
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
