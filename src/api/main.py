import os
import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, Security, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.core.ai import GeminiCore
from src.core.schema import AnalysisResult
from src.core.storage import CloudStorageManager

app = FastAPI(title="Gemini AI Analysis API")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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
async def analyze(
    request: AnalysisRequest,
    api_key: Annotated[str, Security(verify_api_key)],
):
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


@app.post("/analyze-upload", response_model=AnalysisResult)
async def analyze_uploaded_media(
    prompt: Annotated[
        str,
        Form(description="解析用のプロンプト"),
    ],  # multipart形式なのでFormで受け取る
    file: Annotated[
        UploadFile,
        File(description="解析対象のファイル"),
    ],
    api_key: Annotated[
        str,
        Security(verify_api_key),
    ],
) -> AnalysisResult:
    """
    ファイルを直接アップロードし、GCS経由でGemini解析を行う非同期エンドポイント
    """
    # 親となる作業ディレクトリの準備
    upload_root = Path("upload")
    upload_root.mkdir(exist_ok=True)

    # 2. 一時的なサブフォルダを作成し、スコープを抜けると自動削除される仕組み
    # dir=upload_root を指定することで、作業が upload/ 内で完結する
    # エラーが起きても、解析が成功しても、終わった瞬間にtmp_dirフォルダごと消滅
    with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        # 一時フォルダの中にファイルを作成（元ファイルとはパスが必ず異なる）
        local_path = tmp_dir_path / (file.filename or "temp_file")

        try:
            # ローカルに一時保存 (非同期)
            # 巨大なファイルの場合は chunks で回すのが安全
            with local_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # GCSへ非同期アップロード
            storage_manager = CloudStorageManager()
            gcs_uri = await storage_manager.upload_file_async(str(local_path))

            # 4. Geminiで解析 (SKILL.md の非同期パターン)
            # file.content_type (image/png 等) を自動取得して渡す
            result = await ai_core.analyze_image(
                prompt=prompt,
                gcs_uri=gcs_uri,
                response_schema=AnalysisResult,
                mime_type=file.content_type or "image/png",
            )
            return result

        except Exception as e:
            # 失敗時もスキーマに従って success=False で返すか、
            # 深刻なエラーは HTTPException として投げる
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis pipeline failed: {str(e)}",
            ) from e


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def handle_upload(request: Request, file: UploadFile = File(...)):
    # 1. 一時ディレクトリで安全にファイル保存
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = Path(tmp_dir) / (file.filename or "photo.jpg")
        with local_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. GCSへアップロード & Geminiで解析
        storage = CloudStorageManager()
        gcs_uri = await storage.upload_file_async(str(local_path))

        result = await ai_core.analyze_image(
            prompt="この写真に何が写っているか、スマホユーザー向けに短く教えて。",
            gcs_uri=gcs_uri,
            response_schema=AnalysisResult,
            mime_type=file.content_type or "image/jpeg",
        )

    if not result:
        return "<p class='text-red-500'>解析に失敗しました。</p>"

    # 3. htmxに返すHTML断片（ページ全体ではなくここだけが更新される）
    return f"""
    <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
        <h2 class="font-bold text-green-800 mb-1">解析結果</h2>
        <p class="text-gray-700">{result.description}</p>
    </div>
    """
