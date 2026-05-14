from pydantic import BaseModel, Field


class StarEpisode(BaseModel):
    """STAR形式の印象的なエピソード"""

    title: str = Field(description="エピソードのタイトル（一言で）")
    situation: str = Field(description="Situation: 状況・背景")
    task: str = Field(description="Task: 課題・自分の役割")
    action: str = Field(description="Action: 取った行動")
    result: str = Field(description="Result: 結果・学び")


class WorkExperienceNote(BaseModel):
    """職歴ごとの深掘りメモ（ユーザー記入）"""

    company: str = Field(description="会社名（WorkExperienceと同じ値で紐付け）")
    role: str = Field(description="役職名（WorkExperienceと同じ値で紐付け）")
    detail: str = Field(description="面接深掘り用の詳細メモ（自由記述）")


class PersonalProfile(BaseModel):
    """面接対策を「あなたらしく」するためのパーソナルプロフィール"""

    values: list[str] = Field(
        description="価値観・信条のリスト。例: ['自律と信頼', '学び続けること']"
    )
    influential_items: list[str] = Field(
        description="影響を受けた本・人のリスト。例: ['ティール組織', '〇〇さん（元上司）']"
    )
    episodes: list[StarEpisode] = Field(description="印象的なエピソード（STAR形式）のリスト")
    career_vision: str = Field(description="キャリアビジョン（5年後・10年後にどうなりたいか）")
    work_style: str = Field(description="働き方の好み（リモート・裁量・チームのあり方など）")
    work_experience_notes: list[WorkExperienceNote] = Field(
        default=[],
        description="職歴ごとの深掘りメモリスト（面接対策用・ユーザー記入）",
    )


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
    work_experiences: list[WorkExperience] = Field(description="職歴リスト。新しい順に並べること")
    summary: str = Field(
        description="職務経歴の全体サマリー（200字以上）。強み・専門領域・キャリアの方向性を含めること"
    )


class ResumeProfile(BaseModel):
    """職務経歴書から抽出したプロフィール"""

    skills: list[str] = Field(
        description="保有スキル・技術のリスト。例: ['Python', 'SQL', 'プロジェクトマネジメント']"
    )
    work_experiences: list[WorkExperience] = Field(description="職歴リスト。新しい順に並べること")
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
    priority: int = Field(description="アピール優先度。1が最重要で5が最低。1〜5の整数", ge=1, le=5)


class ExperienceMatchList(BaseModel):
    """ExperienceMatchのリストを返すためのラッパー"""

    items: list[ExperienceMatch] = Field(description="マッチング結果リスト（優先度順）")


class ResumeInterviewQuestion(BaseModel):
    """面接で想定される質問と回答例"""

    question: str = Field(description="想定される面接質問（日本語）。行動面接形式を優先すること")
    answer_example: str = Field(
        description="職務経歴の具体的な実績を活かしたSTAR形式の回答例（日本語・200字以上）"
    )
    experience_used: list[str] = Field(description="この回答で活用している職歴・スキルの名称リスト")


class ResumeInterviewQuestionList(BaseModel):
    """ResumeInterviewQuestionのリストを返すためのラッパー"""

    items: list[ResumeInterviewQuestion] = Field(
        description="想定面接質問と回答例のリスト（5〜8件）"
    )


class CompanyFacingQuestion(BaseModel):
    """面接で企業に問いかける逆質問"""

    question: str = Field(description="企業に聞く逆質問（日本語）")
    intent: str = Field(
        description="この質問をする意図と企業に刺さる理由（日本語・100字以上）"
    )
    talking_point: str = Field(
        description="自分の経験・価値観と絡めた話し方のヒント（日本語・100字以上）"
    )


class CompanyFacingQuestionList(BaseModel):
    """CompanyFacingQuestionのリストを返すためのラッパー"""

    items: list[CompanyFacingQuestion] = Field(description="逆質問リスト（5件程度）")


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
    company_profile_id: str | None = Field(
        default=None, description="使用した企業プロフィールID（任意）"
    )
    company_facing_questions: list[CompanyFacingQuestion] | None = Field(
        default=None, description="企業に刺さる逆質問リスト（生成済みの場合のみ）"
    )


class _CompanyPdfExtract(BaseModel):
    """企業PDF資料からのテキスト抽出用内部スキーマ"""

    content: str = Field(
        description="PDF資料から抽出した全内容。企業名・事業・文化・技術・価値観など全情報を網羅すること"
    )


class _CompanyInfoSummary(BaseModel):
    """企業情報統合の内部スキーマ"""

    company_name: str = Field(description="情報ソースから特定した企業名（不明な場合は '不明'）")
    combined_company_info: str = Field(
        description="複数ソースを統合した企業プロフィール（1000〜2000字）。"
        "ミッション・事業内容・技術文化・求める人物像・職場環境等を含む"
    )


class CompanyProfile(BaseModel):
    """複数ソースから収集・統合した企業プロフィール"""

    company_id: str = Field(description="企業プロフィールの一意ID（UUID hex形式）")
    company_name: str | None = Field(default=None, description="企業名")
    hiring_page_url: str | None = Field(default=None, description="採用ページURL")
    tech_blog_urls: list[str] = Field(default=[], description="技術ブログURLリスト")
    employee_interview_urls: list[str] = Field(default=[], description="社員インタビューURLリスト")
    free_text: str | None = Field(default=None, description="その他自由記述（企業情報補足）")
    pdf_gcs_uris: list[str] = Field(default=[], description="企業説明PDFのGCS URIリスト")
    combined_company_info: str = Field(default="", description="AI統合済み企業プロフィールテキスト")
    created_at: str = Field(description="作成日時（ISO 8601形式）")


class InterviewChatRequest(BaseModel):
    """面接チャットのリクエスト"""

    question: str = Field(description="面接で聞かれた（または聞かれそうな）質問")


class InterviewChatResponse(BaseModel):
    """面接チャットのレスポンス"""

    answer: str = Field(description="Geminiが生成した回答アドバイス")
