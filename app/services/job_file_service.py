"""
Enhanced file processing and validation service for job-based workflow
"""
import os
import hashlib
import mimetypes
from typing import Dict, Any, BinaryIO
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

class JobFileService:
    # Supported file types and their media categories
    SUPPORTED_MIMES = {
        # Documents
        'application/pdf': 'document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document',
        'application/msword': 'document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'document',
        'application/vnd.ms-powerpoint': 'document',
        'text/plain': 'document',
        'text/markdown': 'document',
        'application/rtf': 'document',

        # Audio
        'audio/mpeg': 'audio',
        'audio/wav': 'audio',
        'audio/x-wav': 'audio',
        'audio/mp4': 'audio',
        'audio/m4a': 'audio',
        'audio/x-m4a': 'audio',
        'audio/ogg': 'audio',
        'audio/flac': 'audio',

        # Video
        'video/mp4': 'video',
        'video/quicktime': 'video',
        'video/x-msvideo': 'video',
        'video/webm': 'video',
        'video/ogg': 'video',

        # Images (for OCR)
        'image/jpeg': 'image',
        'image/png': 'image',
        'image/tiff': 'image',
        'image/bmp': 'image',
    }

    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'document': 100 * 1024 * 1024,  # 100MB
        'audio': 1000 * 1024 * 1024,   # 1GB
        'video': 2000 * 1024 * 1024,   # 2GB
        'image': 50 * 1024 * 1024,     # 50MB
    }

    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file and return metadata"""

        # Reset file position
        await file.seek(0)

        # Read file content for validation
        content = await file.read()
        file_size = len(content)

        # Reset position again
        await file.seek(0)

        # Use reported MIME type (in production, use python-magic for detection)
        mime_type = file.content_type

        # Validate MIME type
        if mime_type not in self.SUPPORTED_MIMES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {mime_type}. Supported types: {list(self.SUPPORTED_MIMES.keys())}"
            )

        media_type = self.SUPPORTED_MIMES[mime_type]

        # Validate file size
        max_size = self.MAX_FILE_SIZES.get(media_type, 100 * 1024 * 1024)
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size for {media_type} files is {max_size // (1024*1024)}MB"
            )

        # Validate filename
        if not file.filename or len(file.filename) > 255:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )

        # Compute checksum
        checksum = hashlib.sha256(content).hexdigest()

        # Get additional metadata based on media type
        metadata = {
            'mime_type': mime_type,
            'media_type': media_type,
            'size': file_size,
            'checksum': checksum
        }

        # Add media-specific metadata (simplified for demo)
        if media_type == 'document':
            metadata.update(await self._get_document_metadata(content, mime_type))
        elif media_type in ['audio', 'video']:
            # Placeholder - would use ffprobe in production
            metadata['duration_seconds'] = 120.0  # Mock duration

        return metadata

    async def _get_document_metadata(self, content: bytes, mime_type: str) -> Dict[str, Any]:
        """Extract metadata from document files"""
        metadata = {}

        try:
            if mime_type == 'application/pdf':
                # Simplified - would use PyPDF2 in production
                metadata['pages'] = 1
            elif mime_type == 'text/plain':
                # For text files, estimate lines/words
                text = content.decode('utf-8', errors='ignore')
                lines = text.count('\n') + 1
                words = len(text.split())
                metadata.update({'lines': lines, 'words': words})
        except Exception as e:
            logger.warning(f"Could not extract document metadata: {e}")

        return metadata

    def get_file_category(self, filename: str) -> str:
        """Determine file category from filename"""
        mime_type, _ = mimetypes.guess_type(filename)
        return self.SUPPORTED_MIMES.get(mime_type, 'unknown')

    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type in self.SUPPORTED_MIMES

    def generate_safe_filename(self, filename: str) -> str:
        """Generate a safe filename for storage"""
        import re
        import uuid
        from pathlib import Path

        # Get file extension
        path = Path(filename)
        ext = path.suffix.lower()

        # Clean the base name
        base_name = re.sub(r'[^a-zA-Z0-9_-]', '_', path.stem)
        base_name = base_name[:100]  # Limit length

        # Add timestamp/UUID to ensure uniqueness
        unique_id = str(uuid.uuid4())[:8]

        return f"{base_name}_{unique_id}{ext}"