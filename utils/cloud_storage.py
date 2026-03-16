from typing import Optional

import google.auth.transport.requests
from fastapi import UploadFile
from google import auth
from google.cloud import storage
from google.cloud.storage import transfer_manager
from starlette.concurrency import run_in_threadpool


class CloudStorageUtil:

    def __init__(self, realm, gcs_private_bucket_name):
        self.credentials, self.project_id = auth.default()
        self._refresh_credentials()
        self.parent_folder_path = f"{realm}"
        self.private_bucket_name = gcs_private_bucket_name

    def _refresh_credentials(self):
        if not self.credentials.valid:
            self.credentials.refresh(google.auth.transport.requests.Request())
        self.client = storage.Client(credentials=self.credentials)

    async def upload(
        self, file: UploadFile, sub_path: str, file_type: str, file_disposition: str
    ):
        def _sync_upload():
            blob_file_path = self.get_file_path(filename=file.filename, sub_path=sub_path)
            bucket = self.client.bucket(self.private_bucket_name)
            blob = bucket.blob(blob_file_path)
            blob.content_type = file_type
            blob.content_disposition = file_disposition
            blob.upload_from_file(file.file)
            return blob_file_path

        try:
            return await run_in_threadpool(_sync_upload)
        except Exception as e:
            print(f"Error while uploading file e : {e}")
            return None

    async def bulk_upload(self, files: list[UploadFile], sub_path: str) -> list[str]:
        try:
            bucket = self.client.bucket(self.private_bucket_name)
            file_blob_pairs = [
                (
                    file.file,
                    bucket.blob(
                        self.get_file_path(filename=file.filename, sub_path=sub_path)
                    ),
                )
                for file in files
            ]
            response = transfer_manager.upload_many(
                file_blob_pairs=file_blob_pairs, worker_type=transfer_manager.THREAD
            )
            file_paths = [
                self.get_file_path(filename=file.filename, sub_path=sub_path)
                for file in files
            ]
            for idx, (error, file_path) in enumerate(zip(response, file_paths)):
                if error is not None:
                    file_paths[idx] = None
            return file_paths
        except Exception as e:
            return []

    def get_file_path(self, filename: str, sub_path: str):
        return f"{self.parent_folder_path}/{sub_path.strip('/')}/{filename}"

    async def generate_signed_urls(
        self,
        resource_urls: list[str] | str,
        expiration_time: int,
        sign_method: str,
        file_disposition: Optional[str],
    ):
        signed_urls: list = []
        errors: list = []
        self._refresh_credentials()
        bucket = self.client.bucket(self.private_bucket_name)

        if isinstance(resource_urls, str):
            resource_urls = [resource_urls]

        for resource_url in resource_urls:
            signed_url = None
            try:
                blob = bucket.blob(resource_url)
                signed_url = blob.generate_signed_url(
                    version="v4",
                    service_account_email=self.credentials.service_account_email,
                    access_token=self.credentials.token,
                    expiration=expiration_time,
                    method=sign_method,
                    response_disposition=file_disposition,
                )
            except Exception as e:
                print(f"Exception occurred while generating signed URL {str(e)}")
                errors.append({"resource_url": resource_url, "exception": str(e)})
            finally:
                signed_urls.append(signed_url)
        return signed_urls

    async def delete_file(self, blob_path: str) -> bool:
        """
        Delete a file from Google Cloud Storage.

        Args:
            blob_path (str): The full path to the blob in the bucket.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.

        Raises:
            Exception: Re-raised to be handled by the calling service layer.
        """
        def _sync_delete():
            self._refresh_credentials()
            bucket = self.client.bucket(self.private_bucket_name)
            blob = bucket.blob(blob_path)
            
            # Check if blob exists before attempting to delete
            if blob.exists():
                blob.delete()
                return True
            return False

        try:
            return await run_in_threadpool(_sync_delete)
        except Exception as e:
            print(f"Error while deleting file from cloud storage: {e}")
            raise

    async def list_files(self, folder_path: str):
        """
        Lists all files in the specified folder path.
        Returns a list of file information including name, size, and last modified.

        Args:
            folder_path (str): The folder path to list files from.

        Returns:
            list: A list of file dictionaries with metadata.

        Raises:
            Exception: Re-raised to be handled by the calling service layer.
        """
        try:
            self._refresh_credentials()
            bucket = self.client.bucket(self.private_bucket_name)

            # Construct the full folder path with parent folder
            full_folder_path = f"{folder_path.strip('/')}/"



            # List all blobs with the specified prefix
            blobs = bucket.list_blobs(prefix=full_folder_path)

            files = []
            for blob in blobs:
                # Skip folders (blobs ending with /)
                if not blob.name.endswith('/'):
                    # Extract just the filename from the full path
                    filename = blob.name.split('/')[-1]
                    files.append({
                        "name": filename,
                        "size": blob.size,
                        "last_modified": blob.time_created.isoformat() if blob.time_created else None,
                        "content_type": blob.content_type,
                        "full_path": blob.name
                    })


            return files
        except Exception as e:

            # Re-raise the exception to be handled by the service layer
            raise


    async def download_file(self, blob_path: str) -> bytes:
        """
        Download a file from Google Cloud Storage.

        Args:
            blob_path (str): The full path to the blob in the bucket.

        Returns:
            bytes: The downloaded file content.

        Raises:
            Exception: Re-raised to be handled by the calling service layer.
        """

        def _sync_download() -> bytes:
            self._refresh_credentials()
            bucket = self.client.bucket(self.private_bucket_name)
            blob = bucket.blob(blob_path)

            if not blob.exists():
                raise FileNotFoundError(f"Blob not found: {blob_path}")

            return blob.download_as_bytes()

        try:
            return await run_in_threadpool(_sync_download)
        except Exception as e:
            print(f"Error while downloading file from cloud storage: {e}")
            raise


