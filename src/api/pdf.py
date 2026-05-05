import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Security, UploadFile, status
from pydantic import BaseModel

from src.api.auth import verify_api_key
from src.core.ai import GeminiCore
from src.core.storage import CloudStorageManager

router = APIRouter()

_ai_core = GeminiCore()

_EXTRACT_PROMPT = (
    "このPDFに含まれるすべてのテキストを、そのままの順序で抽出してください。"
    "ページ番号やヘッダー・フッターも含め、文章の内容を余さず出力してください。"
    "書式の説明や要約は不要です。テキストだけを出力してください。"
)


class TextExtractionResult(BaseModel):
    text: str
    filename: str


@router.post("/extract-text", response_model=TextExtractionResult)
async def extract_text_from_pdf(
    file: Annotated[UploadFile, File(description="テキスト抽出対象のPDFファイル")],
    api_key: Annotated[str, Security(verify_api_key)],
) -> TextExtractionResult:
    """PDFファイルをアップロードし、Geminiでテキストを抽出して返す。"""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDFファイルのみ対応しています。受信したMIMEタイプ: {file.content_type}",
        )

    upload_root = Path("upload")
    upload_root.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
        tmp_path = Path(tmp_dir) / (file.filename or "document.pdf")
        with tmp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        storage = CloudStorageManager()
        gcs_uri = await storage.upload_file_async(str(tmp_path))

        try:
            text = await _ai_core.analyze_file_simple(
                prompt=_EXTRACT_PROMPT,
                gcs_uri=gcs_uri,
                mime_type="application/pdf",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF解析に失敗しました: {e}",
            ) from e

    return TextExtractionResult(text=text, filename=file.filename or "document.pdf")
