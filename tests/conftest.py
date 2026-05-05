import os
from unittest.mock import MagicMock

# settings = Settings() がモジュールレベルで実行されるため、
# インポート前に環境変数を設定する必要がある
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
os.environ.setdefault("GCS_BUCKET_NAME", "test-bucket")
os.environ.setdefault("BQ_DATASET", "test_dataset")
os.environ.setdefault("BQ_TABLE", "test_table")
os.environ.setdefault("INTERNAL_API_KEY", "test-key")
os.environ.setdefault("FIRESTORE_DATABASE", "(default)")

# テスト時は GCP 認証情報が不要になるよう google.auth.default をモックする。
# FirestoreManager など GCP クライアントはモジュールレベルで初期化されるため、
# テストモジュール収集前にここで差し替えておく必要がある。
import google.auth

_mock_credentials = MagicMock()
_mock_credentials.universe_domain = "googleapis.com"
google.auth.default = lambda *args, **kwargs: (_mock_credentials, "test-project")
