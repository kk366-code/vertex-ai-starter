from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """AI解析結果の構造定義"""

    success: bool = Field(
        description="解析が正常に行われたときはTrue。画像がない・解析不能な場合はFalse。"
    )
    description: str = Field(
        description="画像全体の詳細な日本語説明。解析不能な場合はその理由を説明する。"
    )
    objects: list[str] = Field(
        description="画像内に検知されたオブジェクトのリスト。解析不能な場合は空のリストを返す。"
    )
    confidence_score: float = Field(
        description="解析の信頼度 (0.0-1.0)。解析不能な場合は0.0にする。", ge=0, le=1
    )


# 複数のタスクがある場合は、ここに別のモデルを定義して使い分けます
