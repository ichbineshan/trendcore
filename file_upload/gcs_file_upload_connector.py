from typing import Optional

from fastapi import UploadFile
import io
from config.logging import logger
from config.settings import loaded_config
from file_upload.service import FileService


class GCSFileConnector:

    def __init__(self):
        self.file_service = FileService()
        self.sub_path = loaded_config.image_file_upload_subpath

    async def upload(self, file_bytes: bytearray, file_name: str, file_content_type: str, file_disposition: Optional[str] = None) -> Optional[str]:
        signed_url = None
        if not self.sub_path:
            logger.info("no subpath found in config")
            return signed_url
        try:
            buffer = io.BytesIO(bytes(file_bytes))  # convert to immutable bytes if you like :contentReference[oaicite:5]{index=5}
            buffer.seek(0)
            file_data = UploadFile(file=buffer,filename=file_name)
            signed_url = await self.file_service.upload_file_public(file_data, self.sub_path,file_type=file_content_type,file_disposition=file_disposition)
        except Exception as e:
            logger.error(f"Failed to upload and get file url for agent {file_name}: {e}", exc_info=True)

        return signed_url

