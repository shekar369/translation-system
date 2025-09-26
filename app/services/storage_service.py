"""
MinIO Storage Service for file management
"""
import os
import hashlib
import mimetypes
from typing import BinaryIO, Dict, Any
from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException, UploadFile
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        # MinIO configuration
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET", "translation-jobs")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise

    async def upload_file(self, file: UploadFile, object_key: str) -> Dict[str, Any]:
        """Upload a file to MinIO storage"""
        try:
            # Reset file position
            await file.seek(0)

            # Upload to MinIO
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=file.file,
                length=file.size or -1,
                content_type=file.content_type
            )

            logger.info(f"Uploaded file: {object_key}")

            return {
                "object_key": object_key,
                "etag": result.etag,
                "size": file.size,
                "content_type": file.content_type
            }

        except S3Error as e:
            logger.error(f"Error uploading file {object_key}: {e}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    async def download_file(self, object_key: str) -> BinaryIO:
        """Download a file from MinIO storage"""
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            return response

        except S3Error as e:
            logger.error(f"Error downloading file {object_key}: {e}")
            raise HTTPException(status_code=404, detail=f"File not found: {object_key}")

    async def delete_file(self, object_key: str) -> bool:
        """Delete a file from MinIO storage"""
        try:
            self.client.remove_object(self.bucket_name, object_key)
            logger.info(f"Deleted file: {object_key}")
            return True

        except S3Error as e:
            logger.error(f"Error deleting file {object_key}: {e}")
            return False

    def get_presigned_upload_url(self, object_key: str, expires_in_hours: int = 1) -> str:
        """Generate a presigned URL for direct upload"""
        try:
            from datetime import timedelta

            url = self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                expires=timedelta(hours=expires_in_hours)
            )

            return url

        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_key}: {e}")
            raise HTTPException(status_code=500, detail="Could not generate upload URL")

    def get_presigned_download_url(self, object_key: str, expires_in_hours: int = 24) -> str:
        """Generate a presigned URL for direct download"""
        try:
            from datetime import timedelta

            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                expires=timedelta(hours=expires_in_hours)
            )

            return url

        except S3Error as e:
            logger.error(f"Error generating presigned download URL for {object_key}: {e}")
            raise HTTPException(status_code=500, detail="Could not generate download URL")

    def file_exists(self, object_key: str) -> bool:
        """Check if a file exists in storage"""
        try:
            self.client.stat_object(self.bucket_name, object_key)
            return True
        except S3Error:
            return False

    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file metadata"""
        try:
            stat = self.client.stat_object(self.bucket_name, object_key)
            return {
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type
            }
        except S3Error as e:
            logger.error(f"Error getting file info for {object_key}: {e}")
            raise HTTPException(status_code=404, detail=f"File not found: {object_key}")

    def list_files(self, prefix: str = "") -> list:
        """List files with given prefix"""
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True
            )

            return [
                {
                    "key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                }
                for obj in objects
            ]

        except S3Error as e:
            logger.error(f"Error listing files with prefix {prefix}: {e}")
            return []