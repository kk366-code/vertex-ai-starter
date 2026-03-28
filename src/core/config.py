# from pydantic import Field
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

#     google_cloud_project: str = Field(alias="GOOGLE_CLOUD_PROJECT")

#     google_cloud_location: str = Field(default="asia-northeast1", alias="GOOGLE_CLOUD_LOCATION")

#     gcs_buket_name: str = Field(alias="GCS_BUCKET_NAME")


# settings = Settings()

# from pydantic import AliasChoices, Field
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     # .env ファイルから自動読み込み。型も自動変換される
#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         extra="ignore",  # 定義外の環境変数があっても無視する
#     )

#     # 必須項目 (値がないと起動時に例外を投げる)
#     # google_cloud_project: str = Field(alias="GOOGLE_CLOUD_PROJECT")
#     google_cloud_project: str = Field(
#         validation_alias=AliasChoices("GOOGLE_CLOUD_PROJECT", "project_id")
#     )

#     # デフォルト値付き項目
#     google_cloud_location: str = Field(default="asia-northeast1", alias="GOOGLE_CLOUD_LOCATION")
#     # gcs_bucket_name: str = Field(alias="GCS_BUCKET_NAME")
#     gcs_bucket_name: str = Field(
#         validation_alias=AliasChoices("GCS_BUCKET_NAME", "gcs_bucket_name")
#     )


# # シングルトンとしてインスタンス化
# settings = Settings()


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


# シングルトンとしてインスタンス化
# Pylance の警告が消え、型補完が効くようになります
settings = Settings()  # type: ignore


# from pydantic import Field
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         extra="ignore",
#     )

#     # validation_alias を使うことで、環境変数からの読み込みを静的解析ツールに認識させやすくなります
#     google_cloud_project: str = Field(validation_alias="GOOGLE_CLOUD_PROJECT")
#     google_cloud_location: str = Field(
#         default="asia-northeast1", validation_alias="GOOGLE_CLOUD_LOCATION"
#     )
#     gcs_bucket_name: str = Field(validation_alias="GCS_BUCKET_NAME")


# # それでも警告が出る場合は、型ヒントで「引数なし」を許容させます
# settings = Settings()
