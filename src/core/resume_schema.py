from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    """職歴の1件分"""

    company: str = Field(description="会社名")
    role: str = Field(description="役職・職種名")
    period: str = Field(description="在籍期間。例: '2020年4月 〜 2023年3月'")
    description: str = Field(description="担当業務・役割の説明（日本語）")
    achievements: list[str] = Field(description="主な実績・成果のリスト（日本語）")


class _ResumeProfileExtract(BaseModel):
    """Gemini抽出用の内部スキーマ（raw_textを含まない）"""

    skills: list[str] = Field(
        description="保有スキル・技術のリスト。例: ['Python', 'SQL', 'プロジェクトマネジメント']"
    )
    work_experiences: list[WorkExperience] = Field(
        description="職歴リスト。新しい順に並べること"
    )
    summary: str = Field(
        description="職務経歴の全体サマリー（200字以上）。強み・専門領域・キャリアの方向性を含めること"
    )


class ResumeProfile(BaseModel):
    """職務経歴書から抽出したプロフィール"""

    skills: list[str] = Field(
        description="保有スキル・技術のリスト。例: ['Python', 'SQL', 'プロジェクトマネジメント']"
    )
    work_experiences: list[WorkExperience] = Field(
        description="職歴リスト。新しい順に並べること"
    )
    summary: str = Field(
        description="職務経歴の全体サマリー（200字以上）。強み・専門領域・キャリアの方向性を含めること"
    )
    raw_text: str = Field(description="PDFから抽出した全テキスト（原文ママ）")
    source_gcs_uri: str = Field(description="元となったPDFのGCS URI")


class ExperienceMatch(BaseModel):
    """求人に対するスキル・経験のマッチング結果"""

    skill_or_experience: str = Field(
        description="マッチしたスキルまたは経験の名称。例: 'Python開発経験' / 'チームリード経験'"
    )
    relevance_reason: str = Field(
        description="このスキル・経験が求人にどう活きるかの具体的な説明（日本語・100字以上）"
    )
    priority: int = Field(
        description="アピール優先度。1が最重要で5が最低。1〜5の整数", ge=1, le=5
    )


class ExperienceMatchList(BaseModel):
    """ExperienceMatchのリストを返すためのラッパー"""

    items: list[ExperienceMatch] = Field(description="マッチング結果リスト（優先度順）")


class ResumeInterviewQuestion(BaseModel):
    """面接で想定される質問と回答例"""

    question: str = Field(description="想定される面接質問（日本語）。行動面接形式を優先すること")
    answer_example: str = Field(
        description="職務経歴の具体的な実績を活かしたSTAR形式の回答例（日本語・200字以上）"
    )
    experience_used: list[str] = Field(
        description="この回答で活用している職歴・スキルの名称リスト"
    )


class ResumeInterviewQuestionList(BaseModel):
    """ResumeInterviewQuestionのリストを返すためのラッパー"""

    items: list[ResumeInterviewQuestion] = Field(
        description="想定面接質問と回答例のリスト（5〜8件）"
    )


class ResumeGapAnalysisResult(BaseModel):
    """ギャップ分析とフィットスコアの結果"""

    gap_analysis: str = Field(
        description="職務経歴と求人要件のギャップ分析と対策提案（日本語・300字以上）"
    )
    overall_fit_score: float = Field(
        description="求人との総合適合スコア（0.0〜1.0）", ge=0.0, le=1.0
    )


class ResumeJobAnalysisResult(BaseModel):
    """職務経歴書 × 求人のエージェント分析の最終結果"""

    job_id: str = Field(description="Firestoreドキュメントの一意ID（UUID hex形式）")
    job_posting_company: str = Field(description="企業名")
    job_posting_role: str = Field(description="職種・役職名")
    job_posting_required_skills: list[str] = Field(description="必須・歓迎スキルのリスト")
    job_posting_desired_person: str = Field(description="求める人物像")
    job_posting_culture: str = Field(description="企業文化・職場環境")
    job_posting_raw_text: str = Field(description="求人情報の原文テキスト")
    experience_matches: list[ExperienceMatch] = Field(
        description="求人に対してマッチしたスキル・経験のリスト（優先度順）"
    )
    interview_questions: list[ResumeInterviewQuestion] = Field(
        description="想定面接質問と回答例のリスト（5〜8件）"
    )
    gap_analysis: str = Field(
        description="職務経歴と求人要件のギャップ分析および対策提案（日本語・300字以上）"
    )
    overall_fit_score: float = Field(
        description="求人との総合適合スコア（0.0〜1.0）",
        ge=0.0,
        le=1.0,
    )
    created_at: str = Field(description="分析実行日時（ISO 8601形式）")
