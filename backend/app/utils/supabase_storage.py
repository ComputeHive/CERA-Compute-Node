from typing import Any, Dict, List, Optional

from storage3.types import SignedUploadURL
from supabase import Client, create_client

from app.config import app_config

UNFINISHED_TASKS_BUCKET = "CERA_NODES"
FINISHED_NODES_BUCKET = "NODE_1_OUTPUT"


class SupabaseBlobStorage:

    def __init__(self, supabase_client: Client):
        self.client = supabase_client

    def create_bucket(
        self,
        bucket_id: str,
        bucket_name: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Any:
        return self.client.storage.create_bucket(
            id=bucket_id, name=bucket_name, options=options
        )

    def upload(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> Any:
        return self.client.storage.from_(bucket_name).upload(
            path=object_name, file=data, file_options=options
        )

    def download(self, bucket_name: str, object_name: str) -> bytes:
        return self.client.storage.from_(bucket_name).download(object_name)

    def delete_object(self, bucket_name: str, object_name: str) -> Any:
        return self.client.storage.from_(bucket_name).remove([object_name])

    def generate_presigned_url(
        self, bucket_name: str, object_name: str, expires_in: int = 3600
    ) -> str:
        response = self.client.storage.from_(bucket_name).create_signed_url(
            path=object_name, expires_in=expires_in
        )

        if isinstance(response, dict):
            return response.get("signedUrl", response.get("signedURL", ""))
        return str(response)

    def generate_presigned_upload_url(
        self,
        bucket_name: str,
        object_names: List[str],
    ) -> List[SignedUploadURL]:
        results: List[SignedUploadURL] = []
        for name in object_names:
            response = self.client.storage.from_(
                bucket_name
            ).create_signed_upload_url(path=name)
            results.append(response)
        return results

    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        files = self.client.storage.from_(bucket_name).list()
        return any([f["name"] == object_name for f in files])

    def upload_encrypted_and_get_url(
        self, bucket_name: str, file_name: str, file_bytes: bytes
    ) -> str:
        if self.file_exists(bucket_name, file_name):
            self.delete_object(bucket_name, file_name)
        try:
            self.upload(bucket_name, file_name, file_bytes)
            return self.generate_presigned_url(bucket_name, file_name)
        except Exception:
            try:
                self.delete_object(bucket_name, file_name)
            except Exception as err:
                print(f"Rollback failed for {file_name}: {err}")
            raise


client = create_client(app_config.SUPABASE_URL, app_config.SUPABASE_KEY)
supabase_storage = SupabaseBlobStorage(client)
