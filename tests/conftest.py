import os

# settings = Settings() がモジュールレベルで実行されるため、
# インポート前に環境変数を設定する必要がある
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
os.environ.setdefault("GCS_BUCKET_NAME", "test-bucket")
os.environ.setdefault("BQ_DATASET", "test_dataset")
os.environ.setdefault("BQ_TABLE", "test_table")
os.environ.setdefault("INTERNAL_API_KEY", "test-key")
os.environ.setdefault("FIRESTORE_DATABASE", "(default)")
