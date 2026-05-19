import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Security, UploadFile, status

from src.api.auth import verify_api_key
from src.core.ai import GeminiCore
from src.core.firestore import firestore_manager
from src.core.ocr_schema import OcrPageResult, OcrResult
from src.core.storage import CloudStorageManager

router = APIRouter(prefix="/ocr", tags=["ocr"])

_ai_core = GeminiCore()

_ALLOWED_MIME_TYPES = {"image/png", "image/jpeg"}

_OCR_PROMPT = (
    "この画像に含まれるすべての日本語テキストを、表示されている順序で正確に抽出してください。"
    "改行や段落構造は元の見た目に近い形で保持してください。"
    "ヘッダー・フッター・ページ番号などの周辺UI要素は無視し、本文のみを出力してください。"
    "書式の説明や要約は不要で、テキストだけを出力してください。"
)


def _crop_image(
    src_path: Path,
    dst_path: Path,
    top: int,
    bottom: int,
    left: int,
    right: int,
) -> None:
    """Pillow で固定ピクセル数のクロップ処理を行う。"""
    from PIL import Image

    with Image.open(src_path) as img:
        width, height = img.size
        right_edge = width - right
        bottom_edge = height - bottom
        if right_edge <= left or bottom_edge <= top:
            raise ValueError(
                f"クロップサイズが不正です: {src_path.name} "
                f"(元: {width}x{height}, 余白: top={top}/bottom={bottom}/left={left}/right={right})"
            )
        img.crop((left, top, right_edge, bottom_edge)).save(dst_path)


async def _process_image(
    file: UploadFile,
    page_number: int,
    tmp_dir: Path,
    crop_top: int,
    crop_bottom: int,
    crop_left: int,
    crop_right: int,
) -> OcrPageResult:
    """1 枚の画像を保存・必要ならクロップし、GCS にアップロードして Gemini OCR を行う。"""
    if file.content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"対応していないMIMEタイプです: {file.content_type} "
                f"({file.filename}). PNG または JPEG を指定してください。"
            ),
        )

    original_name = file.filename or f"page_{page_number}.png"
    local_path = tmp_dir / f"{page_number:03d}_{original_name}"
    with local_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    needs_crop = any(v > 0 for v in (crop_top, crop_bottom, crop_left, crop_right))
    if needs_crop:
        cropped_path = tmp_dir / f"cropped_{local_path.name}"
        try:
            _crop_image(local_path, cropped_path, crop_top, crop_bottom, crop_left, crop_right)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        upload_path = cropped_path
    else:
        upload_path = local_path

    storage = CloudStorageManager()
    gcs_uri = await storage.upload_file_async(str(upload_path))

    try:
        text = await _ai_core.analyze_file_simple(
            prompt=_OCR_PROMPT,
            gcs_uri=gcs_uri,
            mime_type=file.content_type or "image/png",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR解析に失敗しました ({original_name}): {e}",
        ) from e

    return OcrPageResult(
        page_number=page_number,
        filename=original_name,
        text=text,
        source_gcs_uri=gcs_uri,
    )


def _build_combined_text(pages: list[OcrPageResult]) -> str:
    """ページマーカー付きの結合テキストを生成する。"""
    return "\n\n".join(f"--- PAGE {p.page_number} ---\n{p.text}" for p in pages)


@router.post("/extract", response_model=OcrResult, status_code=status.HTTP_201_CREATED)
async def extract_text_from_image(
    file: Annotated[UploadFile, File(description="OCR対象の画像ファイル（PNG/JPEG）")],
    api_key: Annotated[str, Security(verify_api_key)],
    crop_top: Annotated[int, Form(ge=0, description="上から削るピクセル数")] = 0,
    crop_bottom: Annotated[int, Form(ge=0, description="下から削るピクセル数")] = 0,
    crop_left: Annotated[int, Form(ge=0, description="左から削るピクセル数")] = 0,
    crop_right: Annotated[int, Form(ge=0, description="右から削るピクセル数")] = 0,
) -> OcrResult:
    """単一画像をアップロードし、GeminiでOCRしてFirestoreに保存する。"""
    upload_root = Path("upload")
    upload_root.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
        page = await _process_image(
            file=file,
            page_number=1,
            tmp_dir=Path(tmp_dir),
            crop_top=crop_top,
            crop_bottom=crop_bottom,
            crop_left=crop_left,
            crop_right=crop_right,
        )

    pages = [page]
    result = OcrResult(
        id=uuid.uuid4().hex,
        combined_text=_build_combined_text(pages),
        pages=pages,
    )
    await firestore_manager.save_ocr_result(result)
    return result


@router.post(
    "/extract-batch",
    response_model=OcrResult,
    status_code=status.HTTP_201_CREATED,
)
async def extract_text_from_images_batch(
    files: Annotated[
        list[UploadFile],
        File(description="OCR対象の画像ファイル一覧（PNG/JPEG、ページ順）"),
    ],
    api_key: Annotated[str, Security(verify_api_key)],
    crop_top: Annotated[int, Form(ge=0, description="上から削るピクセル数")] = 0,
    crop_bottom: Annotated[int, Form(ge=0, description="下から削るピクセル数")] = 0,
    crop_left: Annotated[int, Form(ge=0, description="左から削るピクセル数")] = 0,
    crop_right: Annotated[int, Form(ge=0, description="右から削るピクセル数")] = 0,
) -> OcrResult:
    """複数画像をアップロードし、ページ順にOCRした結果を結合してFirestoreに保存する。"""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="画像ファイルを1枚以上指定してください。",
        )

    upload_root = Path("upload")
    upload_root.mkdir(exist_ok=True)

    pages: list[OcrPageResult] = []
    with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
        tmp_path = Path(tmp_dir)
        for i, file in enumerate(files, start=1):
            page = await _process_image(
                file=file,
                page_number=i,
                tmp_dir=tmp_path,
                crop_top=crop_top,
                crop_bottom=crop_bottom,
                crop_left=crop_left,
                crop_right=crop_right,
            )
            pages.append(page)

    result = OcrResult(
        id=uuid.uuid4().hex,
        combined_text=_build_combined_text(pages),
        pages=pages,
    )
    await firestore_manager.save_ocr_result(result)
    return result


@router.get("/extract/{result_id}", response_model=OcrResult)
async def get_ocr_result(
    result_id: str,
    api_key: Annotated[str, Security(verify_api_key)],
) -> OcrResult:
    """保存済みのOCR結果をIDで取得する。"""
    result = await firestore_manager.get_ocr_result(result_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"指定されたID '{result_id}' のOCR結果が見つかりません。",
        )
    return result
