import io
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Return a boto3 S3 client configured from Django settings."""
    region = settings.AWS_S3_REGION_NAME
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        ),
    )


def upload_file(file_obj, s3_key: str, content_type: str = "application/octet-stream") -> str:
    """
    Upload a file-like object to S3.
    Returns the S3 key on success.
    """
    client = _get_s3_client()
    client.upload_fileobj(
        file_obj,
        settings.AWS_STORAGE_BUCKET_NAME,
        s3_key,
        ExtraArgs={"ContentType": content_type},
    )
    logger.info("Uploaded %s to S3 bucket %s", s3_key, settings.AWS_STORAGE_BUCKET_NAME)
    return s3_key


def upload_bytes(data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
    """Upload raw bytes to S3."""
    return upload_file(io.BytesIO(data), s3_key, content_type)


def download_file(s3_key: str) -> bytes:
    """Download an object from S3 and return its bytes."""
    client = _get_s3_client()
    response = client.get_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=s3_key,
    )
    return response["Body"].read()


def generate_presigned_url(s3_key: str, expiry: int = 3600) -> str:
    """
    Generate a pre-signed URL for downloading an S3 object.
    Default expiry is 1 hour.
    """
    client = _get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": s3_key,
        },
        ExpiresIn=expiry,
    )
    return url


def delete_file(s3_key: str) -> None:
    """Delete an object from S3."""
    if not s3_key:
        return
    client = _get_s3_client()
    try:
        client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_key,
        )
        logger.info("Deleted %s from S3", s3_key)
    except ClientError:
        logger.exception("Failed to delete %s from S3", s3_key)


def build_source_key(project_id: str, doc_id: str, filename: str) -> str:
    """Build S3 key for an uploaded source document."""
    return f"projects/{project_id}/source/{doc_id}_{filename}"


def build_translated_key(project_id: str, doc_id: str, filename: str) -> str:
    """Build S3 key for a translated document."""
    return f"projects/{project_id}/translated/{doc_id}_{filename}"
