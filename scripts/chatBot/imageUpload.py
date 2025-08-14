import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv() 
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = "images"  
LOCAL_IMAGE_FOLDER = "../../data/images"  # 업로드할 로컬 경로


blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

def upload_local_images_to_azure():
    for root, dirs, files in os.walk(LOCAL_IMAGE_FOLDER):
        for file in files:
            if file.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                local_path = os.path.join(root, file)
                
            
                relative_path = os.path.relpath(local_path, LOCAL_IMAGE_FOLDER)
                blob_name = relative_path.replace("\\", "/") 
                
                print(f"Uploading {local_path} as {blob_name}")
                
                blob_client = container_client.get_blob_client(blob_name)
                with open(local_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)

if __name__ == "__main__":
    upload_local_images_to_azure()
    print("success")
