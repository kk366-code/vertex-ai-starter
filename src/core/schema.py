from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """AI解析結果の構造定義"""

    description: str = Field(description="画像全体の詳細な日本語説明")
    objects: list[str] = Field(description="画像内に検知されたオブジェクトのリスト")
    confidence_score: float = Field(description="解析の信頼度 (0.0-1.0)", ge=0, le=1)


# 複数のタスクがある場合は、ここに別のモデルを定義して使い分けます
