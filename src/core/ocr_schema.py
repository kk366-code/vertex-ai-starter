import datetime

from pydantic import BaseModel, Field


class OcrPageResult(BaseModel):
    """1 枚の画像（1 ページ）に対する OCR 結果"""

    page_number: int
    filename: str
    text: str
    source_gcs_uri: str


class OcrResult(BaseModel):
    """OCR 処理の完全な結果（Firestore 保存用 兼 API レスポンス）"""

    id: str
    combined_text: str
    pages: list[OcrPageResult]
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
