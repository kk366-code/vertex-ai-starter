import datetime

from pydantic import BaseModel, Field


class PdfTextResult(BaseModel):
    """PDF テキスト抽出結果"""

    id: str
    text: str
    source_gcs_uri: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
