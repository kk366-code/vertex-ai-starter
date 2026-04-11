import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

import google.cloud.storage as storage
from dotenv import load_dotenv

load_dotenv()


class CloudStorageManager:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        self.client = storage.Client(project=self.project_id)
        # 非同期実行用のスレッドプール
        self._executor = ThreadPoolExecutor(max_workers=4)

    def upload_file(self, source_file_path):
        """ファイルをGCSにアップロードし、gs://から始まるURIを返す"""
        # ファイル名だけを抽出 (upload/test.png -> test.png)
        file_name = os.path.basename(source_file_path)
        gcs_uri = self._upload_logic(source_file_path, file_name)
        return gcs_uri

    async def upload_file_async(self, source_file_path: str) -> str:
        """【非同期版】イベントループをブロックせずにアップロードを実行"""
        file_name = os.path.basename(source_file_path)
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            self._executor,
            self._upload_logic,
            source_file_path,
            file_name,
        )

    def _upload_logic(self, source_path: str, destination_blob_name: str) -> str:
        """
        実際のアップロード処理を行う内部共通ロジック

        Args:
            source_path (str): ローカルのファイルパス
            destination_blob_name (str): GCS上でのオブジェクト名
        Raises:
            ValueError: バケット名が環境変数に設定されていない場合に発生
        """
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME が設定されていません")

        # バケットとBlob（ファイルオブジェクト）の参照を取得
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)

        print(f"Uploading {source_path} to gs://{self.bucket_name}/{destination_blob_name}...")

        # 実際にネットワーク通信が発生する箇所（ブロッキング処理）
        blob.upload_from_filename(source_path)

        return f"gs://{self.bucket_name}/{destination_blob_name}"


if __name__ == "__main__":
    # 動作確認用
    async def run_checks():
        manager = CloudStorageManager()
        test_path = "upload/test.jpg"

        # ディレクトリとテストファイルがなければ作成
        os.makedirs("upload", exist_ok=True)
        if not os.path.exists(test_path):
            with open(test_path, "wb") as f:
                f.write(b"fake image data")

        print("--- Testing Sync Upload ---")
        uri_sync = manager.upload_file(test_path)
        print(f"Sync Success: {uri_sync}")

        print("\n--- Testing Async Upload ---")
        uri_async = await manager.upload_file_async(test_path)
        print(f"Async Success: {uri_async}")

    asyncio.run(run_checks())
