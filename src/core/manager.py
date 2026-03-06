import os

from .ai import GeminiCore
from .storage import CloudStorageManager


class AIFoundation:
    def __init__(self):
        # 環境変数の読み込みを一箇所に集約
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if self.project_id is None:
            raise ValueError("GOOGLE_CLOUD_PROJECT が設定されていません。")

        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")

        self.storage = CloudStorageManager()
        self.ai = GeminiCore(self.project_id, self.location)

    def process_image_analysis(self, local_path: str, prompt: str):
        """
        ローカルファイルをアップロードし、AI解析結果を返す一連のパイプライン
        """
        # 1. ストレージへアップロード
        gcs_uri = self.storage.upload_file(local_path)

        # 2. AIで解析
        # ※ 拡張子からmime_typeを自動判別するロジックをここに入れるとより汎用的
        result = self.ai.generate_json(prompt, gcs_uri=gcs_uri)

        return result
