from typing import Any, Dict, List, Optional

from cera_agent.config import app_config
from storage3.types import SignedUploadURL
from supabase import Client, create_client

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


supabase_client = create_client(
    app_config.SUPABASE_PROJECT, app_config.SUPABASE_KEY
)
supabase_storage = SupabaseBlobStorage(supabase_client)
