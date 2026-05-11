import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from google import genai
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector

from src.core.config import settings

_EMBEDDING_MODEL = "text-multilingual-embedding-002"
_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 100


class EmbeddingCore:
    def __init__(self) -> None:
        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        self._executor = ThreadPoolExecutor(max_workers=4)

    def chunk_text(
        self, text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP
    ) -> list[str]:
        """テキストをオーバーラップ付きでチャンク分割する。"""
        if len(text) <= chunk_size:
            return [text]
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    async def embed_text(self, text: str) -> list[float]:
        """テキストを埋め込みベクトルに変換する（768次元）。"""
        response = await self.client.aio.models.embed_content(
            model=_EMBEDDING_MODEL,
            contents=text,
        )
        if not response.embeddings:
            raise ValueError("埋め込み生成に失敗しました。")
        values = response.embeddings[0].values
        if values is None:
            raise ValueError("埋め込み値がNoneでした。")
        return list(values)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """複数テキストを並列で埋め込みベクトルに変換する。"""
        tasks = [self.embed_text(t) for t in texts]
        return await asyncio.gather(*tasks)

    async def average_embedding(self, texts: list[str]) -> list[float]:
        """複数チャンクの埋め込みを平均して代表ベクトルを生成する。"""
        embeddings = await self.embed_texts(texts)
        arr = np.array(embeddings, dtype=np.float32)
        avg = arr.mean(axis=0)
        norm = np.linalg.norm(avg)
        if norm > 0:
            avg = avg / norm
        return avg.tolist()

    def make_firestore_vector(self, embedding: list[float]) -> Vector:
        return Vector(embedding)

    def make_distance_measure(self) -> DistanceMeasure:
        return DistanceMeasure.COSINE


embedding_core = EmbeddingCore()
