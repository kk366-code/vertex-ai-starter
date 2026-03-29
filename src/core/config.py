from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .envファイルからの自動読み込み設定
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 定義外の変数が .env にあってもエラーにしない
    )

    # フィールド定義: alias を使って環境変数名と紐付ける
    # これにより、Settings() と呼ぶだけで環境変数から値が入る
    google_cloud_project: str = Field(alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="asia-northeast1", alias="GOOGLE_CLOUD_LOCATION")
    gcs_bucket_name: str = Field(alias="GCS_BUCKET_NAME")

    # セキュリティ・認証
    internal_api_key: str = Field(alias="INTERNAL_API_KEY")


# シングルトンとしてインスタンス化
settings = Settings()  # type: ignore
