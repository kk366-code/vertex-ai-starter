from pydantic import BaseModel, Field


class Strength(BaseModel):
    """CliftonStrengthsの1つの強みの定義"""

    name: str = Field(description="強みの日本語名称。例: 'ポジティブ'")
    english_name: str = Field(description="強みの英語名称。例: 'Positivity'")
    domain: str = Field(
        description="強みのドメイン分類。'実行力', '影響力', "
        "'人間関係構築力', '戦略的思考力' のいずれか"
    )
    description: str = Field(description="この強みの特徴と行動傾向の詳細な説明（日本語）")


class StrengthsProfile(BaseModel):
    """ユーザーのCliftonStrengths（ストレングスファインダー）プロフィール全体"""

    top5: list[Strength] = Field(
        description="上位5つの強みのリスト。順位順（1位から5位）に並べること"
    )
    raw_text: str = Field(description="PDFから抽出した全テキスト（原文ママ）")
    source_gcs_uri: str = Field(
        description="元となったPDFのGCS URI。例: 'gs://bucket/strengths.pdf'"
    )


class _JobPostingExtract(BaseModel):
    """Gemini抽出用の内部スキーマ（raw_textを含まない）"""

    company_name: str = Field(description="企業名。例: 'Google Japan'")
    role: str = Field(
        description="求人の職種・役職名。例: 'ソフトウェアエンジニア（バックエンド）'"
    )
    required_skills: list[str] = Field(
        description="必須・歓迎スキルのリスト。例: ['Python', 'SQL', 'システム設計']"
    )
    desired_person: str = Field(description="求める人物像・人柄・マインドセットの説明（日本語）")
    culture: str = Field(description="企業文化・職場環境・働き方の説明（日本語）")


class JobPosting(BaseModel):
    """求人情報の構造化データ"""

    company_name: str = Field(description="企業名。例: 'Google Japan'")
    role: str = Field(
        description="求人の職種・役職名。例: 'ソフトウェアエンジニア（バックエンド）'"
    )
    required_skills: list[str] = Field(
        description="必須・歓迎スキルのリスト。例: ['Python', 'SQL', 'システム設計']"
    )
    desired_person: str = Field(description="求める人物像・人柄・マインドセットの説明（日本語）")
    culture: str = Field(description="企業文化・職場環境・働き方の説明（日本語）")
    raw_text: str = Field(description="求人情報の原文テキスト全体")


class StrengthMatch(BaseModel):
    """求人に対する強みのマッチング結果"""

    strength_name: str = Field(description="マッチした強みの日本語名称。例: 'ポジティブ'")
    relevance_reason: str = Field(
        description="この強みが求人にどう活きるかの具体的な説明（日本語・100字以上）"
    )
    priority: int = Field(
        description="この強みの活用優先度。1が最重要で5が最低。1〜5の整数", ge=1, le=5
    )


class InterviewQuestion(BaseModel):
    """面接で想定される質問と回答例"""

    question: str = Field(description="想定される面接質問（日本語）。行動面接形式を優先すること")
    answer_example: str = Field(
        description="ユーザーの強みを活かしたSTAR形式の具体的な回答例（日本語・200字以上）"
    )
    strengths_used: list[str] = Field(
        description="この回答で活用している強みの日本語名称リスト。例: ['ポジティブ', '学習欲']"
    )


class JobAnalysisResult(BaseModel):
    """求人に対するエージェント分析の最終結果"""

    job_id: str = Field(description="Firestoreドキュメントの一意ID（UUID hex形式）")
    job_posting: JobPosting = Field(description="構造化された求人情報")
    strength_matches: list[StrengthMatch] = Field(
        description="求人に対してマッチした強みのリスト（優先度順）"
    )
    interview_questions: list[InterviewQuestion] = Field(
        description="想定面接質問と回答例のリスト（5〜8件）"
    )
    gap_analysis: str = Field(
        description="強みと求人要件のギャップ分析および対策提案（日本語・300字以上）"
    )
    overall_fit_score: float = Field(
        description="求人との総合適合スコア（0.0〜1.0）。強みの適合度・スキルカバー率・文化フィットを総合判断",
        ge=0.0,
        le=1.0,
    )
    created_at: str = Field(
        description="分析実行日時（ISO 8601形式）。例: '2026-05-03T12:00:00+00:00'"
    )


# --- パイプライン内部用ラッパースキーマ ---
# GeminiはトップレベルがBaseModelである必要があるため、list型を直接返せない


class StrengthMatchList(BaseModel):
    """StrengthMatchのリストを返すためのラッパー"""

    items: list[StrengthMatch] = Field(
        description="求人に対する強みのマッチング結果リスト（優先度順）"
    )


class InterviewQuestionList(BaseModel):
    """InterviewQuestionのリストを返すためのラッパー"""

    items: list[InterviewQuestion] = Field(description="想定面接質問と回答例のリスト（5〜8件）")


class GapAnalysisResult(BaseModel):
    """ギャップ分析とフィットスコアの結果"""

    gap_analysis: str = Field(
        description="強みと求人要件のギャップ分析と対策提案（日本語・300字以上）"
    )
    overall_fit_score: float = Field(
        description="求人との総合適合スコア（0.0〜1.0）", ge=0.0, le=1.0
    )
