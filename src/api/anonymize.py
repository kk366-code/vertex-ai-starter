import asyncio
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Security, status

from src.api.auth import verify_api_key
from src.core.ai import GeminiCore
from src.core.anonymize_methods import (
    anonymize_with_gemini,
    anonymize_with_ollama,
    anonymize_with_regex,
)
from src.core.anonymize_schema import (
    AnonymizeGeminiResult,
    AnonymizeRequest,
    AnonymizeResponse,
    CompareResponse,
)

router = APIRouter(prefix="/anonymize", tags=["anonymize"])
_ai_core = GeminiCore()

# 比較対象の手法リスト。新しい手法を追加する場合はここに追記する。
_AnonymizeMethod = Callable[..., Coroutine[Any, Any, Any]]
_METHODS: list[_AnonymizeMethod] = [
    anonymize_with_regex,
    anonymize_with_gemini,
    anonymize_with_ollama,
]

_ANONYMIZE_PROMPT = """\
【テキスト匿名化タスク】

以下のテキストに含まれる個人情報・機密情報を検出し、匿名化してください。

## 検出カテゴリと置換ルール

| カテゴリ | 対象例 | 置換形式 |
|----------|--------|----------|
| person（人名） | 山田太郎、John Smith | Aさん、Bさん、Cさん … |
| company（会社名） | 株式会社〇〇、〇〇 Inc. | A株式会社/A社（法人格形式に合わせる）、B社 … |
| email（メールアドレス） | user@example.com | a@example.com、b@example.com … |
| phone（電話番号） | 03-1234-5678、090-1234-5678 | 000-0000-0000 |
| address（住所） | 東京都渋谷区〇〇1-2-3 | A都B市C区（都道府県・市区町村・番地を英字記号に置換） |
| other（その他） | マイナンバー、口座番号、パスポート番号 | [機密情報A]、[機密情報B] … |

## ラベル割り当てルール

- カテゴリごとに A, B, C … の順で独立してラベルを割り当てる
  （例: 人名の「A」と会社名の「A」は別カテゴリなので共存してよい）
- 同一の元文字列が複数回出現する場合は、必ず同じ置換文字列を使うこと
- テキストに初めて登場した順番でラベルを割り当てること

## 出力要件

- anonymized_text: 元テキストの構造（改行・句読点・スペース）を保ちつつ、
  上記カテゴリに該当する文字列をすべて置換したテキスト
- entities: 検出したエンティティのリスト（重複なし）
  original は原文の文字列、replacement は実際に置換した文字列
- 検出対象がなければ entities は空リストとし、anonymized_text は元テキストをそのまま返すこと
- テキストに存在しない情報を作り出してはならない

## 対象テキスト

{text}
"""


@router.post("/text", response_model=AnonymizeResponse, status_code=status.HTTP_200_OK)
async def anonymize_text(
    request: AnonymizeRequest,
    api_key: Annotated[str, Security(verify_api_key)],
) -> AnonymizeResponse:
    """
    テキスト中の個人・機密情報（人名、会社名、メール、電話番号、住所等）を
    Geminiで検出し、アルファベット記号のプレースホルダーに置き換えて返す。
    """
    prompt = _ANONYMIZE_PROMPT.format(text=request.text)

    try:
        result: AnonymizeGeminiResult = await _ai_core.analyze_text(
            prompt=prompt,
            response_schema=AnonymizeGeminiResult,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匿名化処理に失敗しました: {e}",
        ) from e

    return AnonymizeResponse(
        original_text=request.text,
        anonymized_text=result.anonymized_text,
        entities=result.entities,
    )


@router.post("/compare", response_model=CompareResponse, status_code=status.HTTP_200_OK)
async def compare_anonymize(
    request: AnonymizeRequest,
    api_key: Annotated[str, Security(verify_api_key)],
) -> CompareResponse:
    """
    複数の匿名化手法を並列実行し、結果を比較できる形式で返す。
    手法の追加は _METHODS リストへの追記のみで対応できる。
    """
    results = await asyncio.gather(
        *[method(text=request.text, ai_core=_ai_core) for method in _METHODS]
    )
    return CompareResponse(original_text=request.text, results=list(results))
