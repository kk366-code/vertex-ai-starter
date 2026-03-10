import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.core.ai import GeminiCore
from src.core.schema import AnalysisResult

app = FastAPI(title="Gemini AI Analysis API")

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if PROJECT_ID is None:
    raise ValueError("環境変数 'GOOGLE_CLOUD_PROJECT' が指定されていません")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
ai_core = GeminiCore(project_id=PROJECT_ID, location=LOCATION)


# リクエストの型定義
class AnalysisRequest(BaseModel):
    prompt: str
    gcs_uri: str | None = None


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(request: AnalysisRequest):
    """
    画像を解析して構造化データを返すエンドポイント
    """
    try:
        if request.gcs_uri:
            # 画像解析
            result = await ai_core.analyze_image(
                prompt=request.prompt, gcs_uri=request.gcs_uri, response_schema=AnalysisResult
            )
        else:
            # テキスト解析
            result = await ai_core.analyze_text(
                prompt=request.prompt, response_schema=AnalysisResult
            )
        return result

    except Exception as e:
        # エラー時は400番や500番のエラーを適切に返す
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health_check():
    return {"status": "ok"}
