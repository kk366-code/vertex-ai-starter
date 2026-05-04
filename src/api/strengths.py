import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Security, UploadFile, status

from src.api.auth import verify_api_key
from src.core.ai import GeminiCore
from src.core.firestore import firestore_manager
from src.core.storage import CloudStorageManager
from src.core.strengths_schema import StrengthsProfile

router = APIRouter(prefix="/strengths", tags=["strengths"])
_ai_core = GeminiCore()


@router.post("/profile", response_model=StrengthsProfile, status_code=status.HTTP_201_CREATED)
async def upload_strengths_profile(
    file: Annotated[UploadFile, File(description="CliftonStrengths結果PDFファイル")],
    api_key: Annotated[str, Security(verify_api_key)],
) -> StrengthsProfile:
    """CliftonStrengths PDFをアップロードし、構造化プロフィールを抽出してFirestoreに保存する"""
    upload_root = Path("upload")
    upload_root.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
        tmp_path = Path(tmp_dir) / (file.filename or "strengths.pdf")
        with tmp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        storage = CloudStorageManager()
        gcs_uri = await storage.upload_file_async(str(tmp_path))

        prompt = (
            "添付のPDFはCliftonStrengths（ストレングスファインダー）の結果レポートです。"
            "上位5つの強みをすべて抽出し、各強みの名前（日本語・英語）、"
            "ドメイン分類（実行力/影響力/人間関係構築力/戦略的思考力のいずれか）、"
            "特徴と行動傾向の説明を構造化して返してください。"
            "top5は1位から5位の順に並べてください。"
            "raw_textフィールドにはPDFの全文テキストをそのまま入れてください。"
            f"source_gcs_uriは '{gcs_uri}' を使用してください。"
        )

        try:
            profile = await _ai_core.analyze_image(
                prompt=prompt,
                gcs_uri=gcs_uri,
                response_schema=StrengthsProfile,
                mime_type="application/pdf",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF解析に失敗しました: {e}",
            ) from e

    await firestore_manager.save_strengths_profile(profile)
    return profile


@router.get("/profile", response_model=StrengthsProfile)
async def get_strengths_profile(
    api_key: Annotated[str, Security(verify_api_key)],
) -> StrengthsProfile:
    """Firestoreに保存済みのStrengthsProfileを取得する"""
    profile = await firestore_manager.get_strengths_profile()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "プロフィールがまだ登録されていません。"
                "POST /strengths/profile でPDFをアップロードしてください。"
            ),
        )
    return profile
