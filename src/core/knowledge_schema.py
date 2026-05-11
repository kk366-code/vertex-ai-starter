from pydantic import BaseModel


class KnowledgeDocument(BaseModel):
    doc_id: str
    title: str
    source_gcs_uri: str
    raw_text: str
    chunks: list[str]
    embedding: list[float]
    created_at: str


class KnowledgeDocumentSummary(BaseModel):
    doc_id: str
    title: str
    source_gcs_uri: str
    created_at: str


class SourceRef(BaseModel):
    doc_id: str
    title: str
    excerpt: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    log_id: str
    query: str
    answer: str
    sources: list[SourceRef]


class SearchFeedbackRequest(BaseModel):
    helpful: bool


class SearchLog(BaseModel):
    log_id: str
    query: str
    answer: str
    source_doc_ids: list[str]
    helpful: bool | None = None
    created_at: str
