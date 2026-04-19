from enum import StrEnum

from pydantic import BaseModel, Field


class ComfortLevel(StrEnum):
    COMFORTABLE = "comfortable"
    WARNING = "warning"
    DANGER = "danger"


class DetectedObject(BaseModel):
    """検知されたオブジェクトの構造定義"""

    name: str = Field(description="オブジェクトの名称。")
    count: int = Field(description="画像内に存在する該当オブジェクトの個数。", ge=1)


class AnalysisResult(BaseModel):
    """AI解析結果の構造定義"""

    success: bool = Field(
        description="解析が正常に行われたときはTrue。画像がない・解析不能な場合はFalse。"
    )
    description: str = Field(
        description="画像全体の詳細な日本語説明。解析不能な場合はその理由を説明する。"
    )
    objects: list[DetectedObject] = Field(
        description="画像内に検知されたオブジェクトのリスト。各要素はname（名称）とcount（個数）を持つ。解析不能な場合は空のリストを返す。"
    )
    confidence_score: float = Field(
        description="解析の信頼度 (0.0-1.0)。解析不能な場合は0.0にする。", ge=0, le=1
    )


class SensorReading(BaseModel):
    """環境センサーの1件の計測データ"""

    sensor_id: str = Field(description="センサーの識別ID。例: 'office-01'")
    type: str = Field(description="センサーの種類。例: 'temperature', 'humidity', 'co2'")
    value: float = Field(description="計測値。温度(℃)、湿度(%)、CO2(ppm) など。")
    timestamp: str = Field(description="計測日時 (ISO 8601形式)。例: '2026-04-12T10:00:00Z'")


class EnvironmentAnalysisResult(BaseModel):
    """環境センサーデータのAI解析結果"""

    success: bool = Field(description="解析が正常に完了した場合はTrue。")
    overall_status: ComfortLevel = Field(description="環境全体の状態。")
    summary: str = Field(description="環境全体の状況を説明する日本語の文章。")
    recommendations: list[str] = Field(
        description="環境改善のための具体的な提案リスト（日本語）。改善不要な場合は空リスト。"
    )
    confidence_score: float = Field(
        description="解析の信頼度 (0.0-1.0)。", ge=0, le=1
    )


# 複数のタスクがある場合は、ここに別のモデルを定義して使い分けます
