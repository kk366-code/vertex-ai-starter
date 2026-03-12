import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from src.core.ai import GeminiCore
from src.core.schema import AnalysisResult

app = FastAPI(title="Gemini AI Analysis API")

# --- 認証設定 ---
load_dotenv()
API_KEY_NAME = "X-API-KEY"
# ヘッダーから X-API-KEY を探す設定
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# 環境変数から「正解のAPIキー」を取得（設定されていない場合はエラー）
EXPECTED_API_KEY = os.getenv("INTERNAL_API_KEY")


async def verify_api_key(api_key: str = Security(api_key_header)):
    """APIキーを検証する依存関数"""
    if not EXPECTED_API_KEY:
        # 開発中の考慮：サーバー側でキーが設定されていない場合
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key is not configured on the server.",
        )
    if api_key != EXPECTED_API_KEY:
        # キーが一致しない場合は 403 Forbidden を返す
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key


# --- 初期化 ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if PROJECT_ID is None:
    raise ValueError("環境変数 'GOOGLE_CLOUD_PROJECT' が指定されていません")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
ai_core = GeminiCore(project_id=PROJECT_ID, location=LOCATION)


# リクエストの型定義
class AnalysisRequest(BaseModel):
    prompt: str
    gcs_uri: str | None = None


# --- エンドポイント ---


@app.post("/analyze", response_model=AnalysisResult | dict)
async def analyze(request: AnalysisRequest, _=Security(verify_api_key)):
    """
    画像を解析して構造化データを返すエンドポイント（要APIキー認証）
    """
    try:
        if request.gcs_uri:
            # 画像解析
            return await ai_core.analyze_image(
                prompt=request.prompt,
                gcs_uri=request.gcs_uri,
                response_schema=AnalysisResult,
            )
        else:
            # テキスト解析（dictが返る）
            answer = await ai_core.analyze_text_simple(
                prompt=request.prompt,
            )
            return {"success": True, "answer": answer}

    except Exception as e:
        # エラー時は400番や500番のエラーを適切に返す
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health_check():
    return {"status": "ok"}
