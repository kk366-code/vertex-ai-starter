import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from src.core.ai import GeminiCore
from src.core.embeddings import embedding_core
from src.core.firestore import firestore_manager
from src.core.knowledge_schema import (
    SearchFeedbackRequest,
    SearchLog,
    SearchRequest,
    SearchResult,
    SourceRef,
)

router = APIRouter(prefix="/search", tags=["search"])

_ai = GeminiCore()

_RAG_PROMPT_TEMPLATE = """\
あなたは過去の業務知見を蓄積したナレッジベースアシスタントです。
以下の関連ドキュメントを参照して、ユーザーの質問に日本語で回答してください。
ドキュメントに記載のない内容は「資料には記載がありません」と回答してください。

【関連ドキュメント】
{context}

【質問】
{query}
"""


@router.post("/query", response_model=SearchResult)
async def search_query(req: SearchRequest) -> SearchResult:
    """クエリをセマンティック検索し、RAGで回答を生成する。"""
    if not req.query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="クエリが空です。")

    query_embedding = await embedding_core.embed_text(req.query)

    docs = await firestore_manager.vector_search_knowledge(query_embedding, limit=req.top_k)
    if not docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ナレッジベースにドキュメントが登録されていません。",
        )

    context_parts: list[str] = []
    sources: list[SourceRef] = []
    for doc in docs:
        excerpt = doc.raw_text[:300].replace("\n", " ")
        context_parts.append(f"[{doc.title}]\n{doc.raw_text[:1500]}")
        sources.append(SourceRef(doc_id=doc.doc_id, title=doc.title, excerpt=excerpt))

    context = "\n\n---\n\n".join(context_parts)
    prompt = _RAG_PROMPT_TEMPLATE.format(context=context, query=req.query)
    answer = await _ai.analyze_text_simple(prompt)

    log_id = uuid.uuid4().hex
    now = datetime.now(UTC).isoformat()
    log = SearchLog(
        log_id=log_id,
        query=req.query,
        answer=answer,
        source_doc_ids=[d.doc_id for d in docs],
        helpful=None,
        created_at=now,
    )
    await firestore_manager.save_search_log(log)

    return SearchResult(log_id=log_id, query=req.query, answer=answer, sources=sources)


@router.post("/feedback/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(log_id: str, req: SearchFeedbackRequest) -> None:
    """検索結果に対するフィードバック（良し悪し）を記録する。"""
    await firestore_manager.update_search_feedback(log_id, req.helpful)
