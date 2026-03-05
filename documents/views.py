import os
import time
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from project.models import Project
from .models import Document, TranslationLog
from .enums import DocumentStatus, FILE_EXTENSION_MAP
from .serializers import (
    DocumentUploadSerializer,
    DocumentListSerializer,
    DocumentDetailSerializer,
)
from .permissions import CanAccessProjectDocuments, CanDeleteDocument
from . import storage
from .parsers import parse_file
from .generators import generate_translated_file
from .translators import get_translator

logger = logging.getLogger(__name__)


class DocumentListCreateView(APIView):

    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [IsAuthenticated(), CanAccessProjectDocuments()]


    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        documents = Document.objects.filter(project=project).select_related("uploaded_by")
        serializer = DocumentDetailSerializer(documents, many=True)
        return Response(serializer.data)


    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        upload_ser = DocumentUploadSerializer(data=request.data)
        upload_ser.is_valid(raise_exception=True)
        uploaded_file = upload_ser.validated_data["file"]

        filename = uploaded_file.name
        ext = os.path.splitext(filename)[1].lower()
        file_type = FILE_EXTENSION_MAP[ext]
        file_bytes = uploaded_file.read()

        # 2. Create Document record (status = UPLOADED)
        doc = Document.objects.create(
            project=project,
            uploaded_by=request.user,
            original_filename=filename,
            file_type=file_type,
            file_size=len(file_bytes),
            status=DocumentStatus.UPLOADED,
        )

        # 3. Upload source file to S3
        source_key = storage.build_source_key(str(project.id), str(doc.id), filename)
        try:
            storage.upload_bytes(file_bytes, source_key, uploaded_file.content_type or "application/octet-stream")
            doc.source_s3_key = source_key
            doc.save(update_fields=["source_s3_key"])
        except Exception as exc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = f"S3 upload failed: {exc}"
            doc.save(update_fields=["status", "error_message"])
            return Response(
                DocumentDetailSerializer(doc).data,
                status=status.HTTP_201_CREATED,
            )

        # 4. Parse text from file
        try:
            extracted_text = parse_file(file_bytes, file_type)
        except Exception as exc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = f"File parsing failed: {exc}"
            doc.save(update_fields=["status", "error_message"])
            return Response(
                DocumentDetailSerializer(doc).data,
                status=status.HTTP_201_CREATED,
            )

        # 5. Translate synchronously
        doc.status = DocumentStatus.TRANSLATING
        doc.save(update_fields=["status"])

        translator = get_translator()
        start_time = time.time()

        try:
            translated_text = translator.translate(
                extracted_text,
                source_lang=doc.source_language,
                target_lang=doc.target_language,
            )
            duration_ms = int((time.time() - start_time) * 1000)
        except Exception as exc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = f"Translation failed: {exc}"
            doc.save(update_fields=["status", "error_message"])
            return Response(
                DocumentDetailSerializer(doc).data,
                status=status.HTTP_201_CREATED,
            )

        # 6. Generate translated output file in the same format
        try:
            translated_bytes, translated_content_type = generate_translated_file(
                translated_text, file_type, filename
            )
        except Exception as exc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = f"Output file generation failed: {exc}"
            doc.save(update_fields=["status", "error_message"])
            return Response(
                DocumentDetailSerializer(doc).data,
                status=status.HTTP_201_CREATED,
            )

        # 7. Upload translated file to S3
        translated_filename = f"translated_{filename}"
        translated_key = storage.build_translated_key(
            str(project.id), str(doc.id), translated_filename
        )
        try:
            storage.upload_bytes(translated_bytes, translated_key, translated_content_type)
            doc.translated_s3_key = translated_key
            doc.status = DocumentStatus.COMPLETED
            doc.save(update_fields=["translated_s3_key", "status"])
        except Exception as exc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = f"Translated file S3 upload failed: {exc}"
            doc.save(update_fields=["status", "error_message"])
            return Response(
                DocumentDetailSerializer(doc).data,
                status=status.HTTP_201_CREATED,
            )

        # 8. Create translation log
        TranslationLog.objects.create(
            document=doc,
            engine_used=translator.engine_name,
            char_count=len(extracted_text),
            duration_ms=duration_ms,
        )

        return Response(
            DocumentDetailSerializer(doc).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    """
    GET    — document detail with presigned download URLs.
    DELETE — remove document + S3 files (Admin/Manager only).
    """

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), CanAccessProjectDocuments(), CanDeleteDocument()]
        return [IsAuthenticated(), CanAccessProjectDocuments()]

    def get(self, request, project_id, doc_id):
        doc = get_object_or_404(Document, id=doc_id, project_id=project_id)
        return Response(DocumentDetailSerializer(doc).data)

    def delete(self, request, project_id, doc_id):
        doc = get_object_or_404(Document, id=doc_id, project_id=project_id)

        # Clean up S3
        storage.delete_file(doc.source_s3_key)
        storage.delete_file(doc.translated_s3_key)

        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentDownloadView(APIView):
    """
    GET — redirect to a presigned S3 URL for source or translated file.
    URL: .../download/source/ or .../download/translated/
    """

    def get_permissions(self):
        return [IsAuthenticated(), CanAccessProjectDocuments()]

    def get(self, request, project_id, doc_id, file_kind):
        doc = get_object_or_404(Document, id=doc_id, project_id=project_id)

        if file_kind == "source":
            key = doc.source_s3_key
        elif file_kind == "translated":
            key = doc.translated_s3_key
        else:
            return Response(
                {"detail": "Invalid file kind. Use 'source' or 'translated'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not key:
            return Response(
                {"detail": f"No {file_kind} file available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        url = storage.generate_presigned_url(key)
        return Response({"download_url": url})
