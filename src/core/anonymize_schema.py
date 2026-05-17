from pydantic import BaseModel, Field


class DetectedEntity(BaseModel):
    original: str = Field(description="元テキストから抽出した個人・機密情報（原文ママ）")
    category: str = Field(
        description=(
            "情報カテゴリ。必ず以下のいずれか: "
            "'person'（人名）, 'company'（会社名）, 'email'（メールアドレス）, "
            "'phone'（電話番号）, 'address'（住所）, 'other'（その他の機密情報）"
        )
    )
    replacement: str = Field(description="実際に匿名化テキスト内で使用した置換文字列")


class AnonymizeGeminiResult(BaseModel):
    anonymized_text: str = Field(
        description=(
            "元テキストの個人・機密情報をすべて置換した匿名化済みテキスト。"
            "同一エンティティが複数回出現する場合は同じ置換文字列を一貫して使用すること。"
            "テキスト全体の構造・改行・句読点は原文通りに保つこと。"
        )
    )
    entities: list[DetectedEntity] = Field(
        description=(
            "検出した個人・機密情報のリスト（重複なし）。"
            "同一の原文が複数箇所に出現する場合は1エントリのみ登録すること。"
            "検出対象がなければ空リストを返すこと。"
        )
    )


class AnonymizeRequest(BaseModel):
    text: str = Field(description="匿名化対象のテキスト（日本語・英語どちらも可）")


class AnonymizeResponse(BaseModel):
    original_text: str = Field(description="入力された元のテキスト")
    anonymized_text: str = Field(description="匿名化済みテキスト")
    entities: list[DetectedEntity] = Field(
        description="検出された個人・機密情報と置換文字列のマッピングリスト"
    )


class MethodResult(BaseModel):
    method: str = Field(description="手法名（regex / gemini / ollama など）")
    label: str = Field(description="表示用ラベル")
    anonymized_text: str = Field(description="匿名化済みテキスト")
    entities: list[DetectedEntity] = Field(description="検出エンティティ一覧")
    duration_ms: int = Field(description="処理時間（ミリ秒）")
    error: str | None = Field(default=None, description="エラーメッセージ（失敗時のみ）")


class CompareResponse(BaseModel):
    original_text: str = Field(description="入力された元のテキスト")
    results: list[MethodResult] = Field(description="各手法の結果一覧")
