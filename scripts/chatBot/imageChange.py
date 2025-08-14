from azure.storage.blob import BlobServiceClient, ContentSettings
import os
import mimetypes
from dotenv import load_dotenv

load_dotenv() 
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = "images"

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(container_name)

for blob in container_client.list_blobs():
    if blob.name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        blob_client = container_client.get_blob_client(blob)

        mime_type, _ = mimetypes.guess_type(blob.name)
        if not mime_type:
            mime_type = "application/octet-stream"  # fallback

        print(f"🔧 {blob.name} → {mime_type} 설정 중...")

        blob_client.set_http_headers(
            content_settings=ContentSettings(
                content_type=mime_type,
                content_disposition="inline"
            )
        )
