import os

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()


class CloudStorageManager:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        self.client = storage.Client(project=self.project_id)

    def upload_file(self, source_file_path):
        """ファイルをGCSにアップロードし、gs://から始まるURIを返す"""
        # ファイル名だけを抽出 (upload/test.png -> test.png)
        file_name = os.path.basename(source_file_path)

        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(file_name)

        print(f"Uploading {source_file_path} to gs://{self.bucket_name}/{file_name}...")
        blob.upload_from_filename(source_file_path)

        return f"gs://{self.bucket_name}/{file_name}"


if __name__ == "__main__":
    # 動作確認用
    manager = CloudStorageManager()
    # 実際のパスを指定
    gcs_uri = manager.upload_file("upload/test.png")
    print(f"Success! GCS URI: {gcs_uri}")
