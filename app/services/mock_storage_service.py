"""
Mock Storage Service for testing without MinIO
"""
import os
import shutil
import json
from typing import BinaryIO, Dict, Any
from fastapi import HTTPException, UploadFile
import logging
import io

logger = logging.getLogger(__name__)

class MockStorageService:
    def __init__(self):
        # Mock storage configuration
        self.storage_path = "storage/mock_minio"
        self.mock_mode = True

        # Create storage directory
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"✅ Mock storage initialized at {self.storage_path}")

    async def upload_file(self, file: UploadFile, object_key: str) -> Dict[str, Any]:
        """Upload a file to mock storage"""
        try:
            # Create directory structure
            file_path = os.path.join(self.storage_path, object_key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Reset file position
            await file.seek(0)

            # Save file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            logger.info(f"Uploaded file to mock storage: {object_key}")

            return {
                "object_key": object_key,
                "etag": "mock-etag",
                "size": file.size,
                "content_type": file.content_type
            }

        except Exception as e:
            logger.error(f"Error uploading file {object_key}: {e}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    async def download_file(self, object_key: str) -> BinaryIO:
        """Download a file from mock storage"""
        try:
            file_path = os.path.join(self.storage_path, object_key)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"File not found: {object_key}")

            with open(file_path, "rb") as f:
                content = f.read()

            return io.BytesIO(content)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error downloading file {object_key}: {e}")
            raise HTTPException(status_code=404, detail=f"File not found: {object_key}")

    async def delete_file(self, object_key: str) -> bool:
        """Delete a file from mock storage"""
        try:
            file_path = os.path.join(self.storage_path, object_key)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file from mock storage: {object_key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting file {object_key}: {e}")
            return False

    def get_presigned_upload_url(self, object_key: str, expires_in_hours: int = 1) -> str:
        """Generate a mock presigned URL for direct upload"""
        # For mock, return a simple URL pattern
        return f"http://localhost:8000/api/mock-upload/{object_key}"

    def get_presigned_download_url(self, object_key: str, expires_in_hours: int = 24) -> str:
        """Generate a mock presigned URL for direct download"""
        return f"http://localhost:8000/api/mock-download/{object_key}"

    def file_exists(self, object_key: str) -> bool:
        """Check if a file exists in mock storage"""
        file_path = os.path.join(self.storage_path, object_key)
        return os.path.exists(file_path)

    def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file metadata from mock storage"""
        file_path = os.path.join(self.storage_path, object_key)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {object_key}")

        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "etag": "mock-etag",
            "last_modified": stat.st_mtime,
            "content_type": "application/octet-stream"
        }

    def list_files(self, prefix: str = "") -> list:
        """List files with given prefix in mock storage"""
        try:
            files = []
            prefix_path = os.path.join(self.storage_path, prefix) if prefix else self.storage_path

            if os.path.exists(prefix_path):
                for root, dirs, filenames in os.walk(prefix_path):
                    for filename in filenames:
                        full_path = os.path.join(root, filename)
                        relative_path = os.path.relpath(full_path, self.storage_path)
                        relative_path = relative_path.replace("\\", "/")  # Use forward slashes

                        stat = os.stat(full_path)
                        files.append({
                            "key": relative_path,
                            "size": stat.st_size,
                            "last_modified": stat.st_mtime,
                            "etag": "mock-etag"
                        })

            return files

        except Exception as e:
            logger.error(f"Error listing files with prefix {prefix}: {e}")
            return []