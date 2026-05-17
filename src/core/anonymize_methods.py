"""
匿名化手法の実装。各手法は同じシグネチャを持つ非同期関数。
新しい手法を追加する場合:
  1. この関数と同じシグネチャで関数を定義する
  2. anonymize.py の METHODS リストに追加する
"""

import re
import time
from functools import lru_cache
from string import ascii_uppercase

import httpx

from src.core.ai import GeminiCore
from src.core.anonymize_schema import AnonymizeGeminiResult, DetectedEntity, MethodResult

# GiNZA ラベル → 匿名化カテゴリのマッピング
_GINZA_LABEL_MAP: dict[str, str] = {
    "Person": "person",
    "N_Person": "person",
    "Company": "company",
    "Company_Group": "company",
    "Corporation_Other": "company",
    "N_Organization": "company",
    "Organization_Other": "company",
    "International_Organization": "company",
    "Political_Organization_Other": "company",
    "Province": "address",
    "City": "address",
    "Country": "address",
    "Postal_Address": "address",
    "Domestic_Region": "address",
    "GPE_Other": "address",
    "Location_Other": "address",
    "Email": "email",
    "Phone_Number": "phone",
    "ID_Number": "other",
    "URL": "other",
}


# カテゴリ別の置換文字列生成ルール
def _make_replacement(category: str, label: str) -> str:
    if category == "person":
        return f"{label}さん"
    if category == "company":
        return f"{label}社"
    if category == "email":
        return f"{label.lower()}@example.com"
    if category == "phone":
        return "000-0000-0000"
    if category == "address":
        return f"[住所{label}]"
    return f"[機密情報{label}]"


@lru_cache(maxsize=1)
def _load_ginza():
    import spacy

    return spacy.load("ja_ginza", exclude=["compound_splitter", "bunsetu_recognizer"])


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
- 同一の元文字列が複数回出現する場合は、必ず同じ置換文字列を使うこと
- テキストに初めて登場した順番でラベルを割り当てること

## 出力要件

- anonymized_text: 元テキストの構造（改行・句読点・スペース）を保ちつつ置換したテキスト
- entities: 検出したエンティティのリスト（重複なし）
- 検出対象がなければ entities は空リストとし、anonymized_text は元テキストをそのまま返すこと

## 対象テキスト

{text}
"""

# --- 正規表現パターン ---
_EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")
_PHONE_RE = re.compile(r"0\d{1,4}[-\s]\d{2,4}[-\s]\d{4}")


def _regex_replace_emails(text: str) -> tuple[str, list[DetectedEntity]]:
    entities: list[DetectedEntity] = []
    seen: dict[str, str] = {}
    labels = iter("abcdefghijklmnopqrstuvwxyz")

    def _replace(m: re.Match) -> str:
        original = m.group()
        if original not in seen:
            label = next(labels, "z")
            seen[original] = f"{label}@example.com"
            entities.append(
                DetectedEntity(original=original, category="email", replacement=seen[original])
            )
        return seen[original]

    return _EMAIL_RE.sub(_replace, text), entities


def _regex_replace_phones(text: str) -> tuple[str, list[DetectedEntity]]:
    entities: list[DetectedEntity] = []
    seen: dict[str, str] = {}

    def _replace(m: re.Match) -> str:
        original = m.group()
        if original not in seen:
            seen[original] = "000-0000-0000"
            entities.append(
                DetectedEntity(original=original, category="phone", replacement="000-0000-0000")
            )
        return seen[original]

    return _PHONE_RE.sub(_replace, text), entities


async def anonymize_with_regex(text: str, **_) -> MethodResult:
    start = time.monotonic()
    try:
        result, email_entities = _regex_replace_emails(text)
        result, phone_entities = _regex_replace_phones(result)
        entities = email_entities + phone_entities
        duration_ms = int((time.monotonic() - start) * 1000)
        return MethodResult(
            method="regex",
            label="正規表現",
            anonymized_text=result,
            entities=entities,
            duration_ms=duration_ms,
        )
    except Exception as e:
        return MethodResult(
            method="regex",
            label="正規表現",
            anonymized_text=text,
            entities=[],
            duration_ms=int((time.monotonic() - start) * 1000),
            error=str(e),
        )


async def anonymize_with_gemini(text: str, ai_core: GeminiCore, **_) -> MethodResult:
    start = time.monotonic()
    try:
        prompt = _ANONYMIZE_PROMPT.format(text=text)
        result: AnonymizeGeminiResult = await ai_core.analyze_text(
            prompt=prompt,
            response_schema=AnonymizeGeminiResult,
        )
        return MethodResult(
            method="gemini",
            label="Gemini 2.5 Flash",
            anonymized_text=result.anonymized_text,
            entities=result.entities,
            duration_ms=int((time.monotonic() - start) * 1000),
        )
    except Exception as e:
        return MethodResult(
            method="gemini",
            label="Gemini 2.5 Flash",
            anonymized_text=text,
            entities=[],
            duration_ms=int((time.monotonic() - start) * 1000),
            error=str(e),
        )


async def anonymize_with_ginza(text: str, **_) -> MethodResult:
    start = time.monotonic()
    try:
        nlp = _load_ginza()
        doc = nlp(text)

        # カテゴリ別に A, B, C … のラベルを独立採番
        category_counters: dict[str, int] = {}
        seen: dict[str, str] = {}
        entities: list[DetectedEntity] = []

        result = text
        # 後ろから置換して位置ずれを防ぐ
        for ent in sorted(doc.ents, key=lambda e: e.start_char, reverse=True):
            category = _GINZA_LABEL_MAP.get(ent.label_)
            if category is None:
                continue
            original = ent.text
            if original not in seen:
                idx = category_counters.get(category, 0)
                label = ascii_uppercase[idx] if idx < 26 else f"A{idx}"
                category_counters[category] = idx + 1
                replacement = _make_replacement(category, label)
                seen[original] = replacement
                entities.append(
                    DetectedEntity(original=original, category=category, replacement=replacement)
                )
            result = result[: ent.start_char] + seen[original] + result[ent.end_char :]

        entities.sort(key=lambda e: text.index(e.original))
        return MethodResult(
            method="ginza",
            label="GiNZA (NER)",
            anonymized_text=result,
            entities=entities,
            duration_ms=int((time.monotonic() - start) * 1000),
        )
    except Exception as e:
        return MethodResult(
            method="ginza",
            label="GiNZA (NER)",
            anonymized_text=text,
            entities=[],
            duration_ms=int((time.monotonic() - start) * 1000),
            error=str(e),
        )


async def anonymize_with_ollama(text: str, model: str = "llama3.2", **_) -> MethodResult:
    """
    ローカルLLM（Ollama）を使った匿名化。
    Ollamaが起動していない場合はエラーとして返す。
    起動方法: ollama serve && ollama pull llama3.2
    """
    start = time.monotonic()
    prompt = _ANONYMIZE_PROMPT.format(text=text) + "\n\nJSON形式のみで出力してください。"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
            )
            res.raise_for_status()
            raw = res.json().get("response", "")

        parsed = AnonymizeGeminiResult.model_validate_json(raw)
        return MethodResult(
            method="ollama",
            label=f"Ollama ({model})",
            anonymized_text=parsed.anonymized_text,
            entities=parsed.entities,
            duration_ms=int((time.monotonic() - start) * 1000),
        )
    except httpx.ConnectError:
        return MethodResult(
            method="ollama",
            label=f"Ollama ({model})",
            anonymized_text=text,
            entities=[],
            duration_ms=int((time.monotonic() - start) * 1000),
            error="Ollamaが起動していません。`ollama serve` を実行してください。",
        )
    except Exception as e:
        return MethodResult(
            method="ollama",
            label=f"Ollama ({model})",
            anonymized_text=text,
            entities=[],
            duration_ms=int((time.monotonic() - start) * 1000),
            error=str(e),
        )
