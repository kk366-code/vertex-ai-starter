import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.core.ai import GeminiCore
from src.core.embeddings import embedding_core
from src.core.firestore import firestore_manager
from src.core.knowledge_schema import KnowledgeDocument, KnowledgeDocumentSummary
from src.core.storage import CloudStorageManager

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_ai = GeminiCore()
_storage = CloudStorageManager()

_PDF_EXTRACT_PROMPT = (
    "このPDFの全テキストをそのまま抽出してください。"
    "構造（見出し・箇条書き・段落）をできるだけ保持し、図表の説明も含めてください。"
)


@router.post(
    "/documents", response_model=KnowledgeDocumentSummary, status_code=status.HTTP_201_CREATED
)
async def upload_knowledge_document(
    file: Annotated[UploadFile, File(description="登録するPDFファイル")],
) -> KnowledgeDocumentSummary:
    """PDFをナレッジベースに登録する。テキスト抽出→チャンク分割→埋め込み生成→Firestore保存。"""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDFファイルのみ対応しています。",
        )

    upload_root = Path("upload")
    upload_root.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
        local_path = Path(tmp_dir) / (file.filename or "document.pdf")
        with local_path.open("wb") as buf:
            shutil.copyfileobj(file.file, buf)

        gcs_uri = await _storage.upload_file_async(str(local_path))

    raw_text = await _ai.analyze_file_simple(
        prompt=_PDF_EXTRACT_PROMPT,
        gcs_uri=gcs_uri,
        mime_type="application/pdf",
    )

    chunks = embedding_core.chunk_text(raw_text)
    embedding = await embedding_core.average_embedding(chunks)

    doc_id = uuid.uuid4().hex
    now = datetime.now(UTC).isoformat()
    title = Path(file.filename or "document.pdf").stem

    doc = KnowledgeDocument(
        doc_id=doc_id,
        title=title,
        source_gcs_uri=gcs_uri,
        raw_text=raw_text,
        chunks=chunks,
        embedding=embedding,
        created_at=now,
    )
    await firestore_manager.save_knowledge_document(doc)

    return KnowledgeDocumentSummary(
        doc_id=doc_id,
        title=title,
        source_gcs_uri=gcs_uri,
        created_at=now,
    )


@router.get("/documents", response_model=list[KnowledgeDocumentSummary])
async def list_knowledge_documents() -> list[KnowledgeDocumentSummary]:
    """登録済みナレッジドキュメントの一覧を返す。"""
    return await firestore_manager.list_knowledge_documents()


@router.get("/documents/{doc_id}", response_model=KnowledgeDocument)
async def get_knowledge_document(doc_id: str) -> KnowledgeDocument:
    """指定IDのナレッジドキュメントを返す。"""
    doc = await firestore_manager.get_knowledge_document(doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ドキュメントが見つかりません。"
        )
    return doc


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_document(doc_id: str) -> None:
    """指定IDのナレッジドキュメントをFirestoreおよびGCSから削除する。"""
    doc = await firestore_manager.get_knowledge_document(doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ドキュメントが見つかりません。"
        )
    await firestore_manager.delete_knowledge_document(doc_id)
    await _storage.delete_file_async(doc.source_gcs_uri)
