import json

from fastapi.testclient import TestClient

from src.core.ai import GeminiCore
from src.core.resume_schema import (
    CompanyFacingQuestion,
    CompanyFacingQuestionList,
    ExperienceMatch,
    ResumeInterviewQuestion,
    ResumeJobAnalysisResult,
    ResumeProfile,
    WorkExperience,
)

# --- テスト用フィクスチャ ---

SAMPLE_RESUME_PROFILE = ResumeProfile(
    skills=["Python", "FastAPI", "SQL"],
    work_experiences=[
        WorkExperience(
            company="テスト株式会社",
            role="バックエンドエンジニア",
            period="2021年4月 〜 現在",
            description="FastAPIを用いたAPIサーバーの開発",
            achievements=["API応答速度を30%改善", "CI/CDパイプラインを構築"],
        )
    ],
    summary="PythonとFastAPIを中心に3年間バックエンド開発に従事。" * 5,
    raw_text="原文テキスト",
    source_gcs_uri="gs://bucket/resume.pdf",
)

SAMPLE_JOB_ANALYSIS = ResumeJobAnalysisResult(
    job_id="abc123",
    job_posting_company="サンプル株式会社",
    job_posting_role="シニアエンジニア",
    job_posting_required_skills=["Python", "AWS"],
    job_posting_desired_person="自律的に動ける方",
    job_posting_culture="フラットな組織",
    job_posting_raw_text="求人情報の原文",
    experience_matches=[
        ExperienceMatch(
            skill_or_experience="Python開発経験",
            relevance_reason="バックエンド開発の主力言語として直接活用できる",
            priority=1,
        )
    ],
    interview_questions=[
        ResumeInterviewQuestion(
            question="これまでの開発で最も困難だった課題は？",
            answer_example="FastAPIの導入時に..." * 10,
            experience_used=["バックエンドエンジニア"],
        )
    ],
    gap_analysis="スキルと要件のギャップ分析：" * 15,
    overall_fit_score=0.75,
    created_at="2026-05-07T10:00:00+00:00",
    company_profile_id=None,
)

SAMPLE_COMPANY_QUESTIONS = CompanyFacingQuestionList(
    items=[
        CompanyFacingQuestion(
            question="御社のエンジニアチームが直面している最大の技術的課題は何ですか？",
            intent="技術的課題への理解を示し、入社後に貢献できる意欲を伝えられる。" * 3,
            talking_point="自分がAPI開発で直面した課題と絡めて質問することで、具体性が増す。" * 3,
        ),
        CompanyFacingQuestion(
            question="新しい技術を採用する際の意思決定プロセスを教えてください。",
            intent="技術選定への関心と組織の意思決定文化を理解しようとする姿勢が伝わる。" * 3,
            talking_point="自分がFastAPIを導入した経験と絡めて、主体的な姿勢を示せる。" * 3,
        ),
    ]
)


def _make_mock_response(data: dict, mocker) -> object:
    mock_resp = mocker.MagicMock()
    mock_resp.text = json.dumps(data, ensure_ascii=False)
    return mock_resp


# --- テスト ---


async def test_generate_company_questions_success(mocker):
    """正常系: 逆質問が生成されてFirestoreに保存され、リストが返ること"""
    mocker.patch(
        "src.api.resume.firestore_manager.get_resume_job_analysis",
        return_value=SAMPLE_JOB_ANALYSIS,
    )
    mocker.patch(
        "src.api.resume.firestore_manager.get_resume_profile",
        return_value=SAMPLE_RESUME_PROFILE,
    )
    mocker.patch(
        "src.api.resume.firestore_manager.get_personal_profile",
        return_value=None,
    )
    mock_save = mocker.patch(
        "src.api.resume.firestore_manager.save_resume_job_analysis",
        return_value="abc123",
    )

    core = GeminiCore(project_id="test-project", location="asia-northeast1")
    mocker.patch.object(
        core.client.aio.models,
        "generate_content",
        new_callable=mocker.AsyncMock,
        return_value=_make_mock_response(SAMPLE_COMPANY_QUESTIONS.model_dump(), mocker),
    )
    mocker.patch("src.api.resume._ai_core", core)
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/resume/jobs/abc123/company-questions",
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["question"] == SAMPLE_COMPANY_QUESTIONS.items[0].question
    assert mock_save.called


async def test_generate_company_questions_job_not_found(mocker):
    """job_idが存在しない場合に404が返ること"""
    mocker.patch(
        "src.api.resume.firestore_manager.get_resume_job_analysis",
        return_value=None,
    )
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/resume/jobs/nonexistent/company-questions",
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 404


async def test_generate_company_questions_profile_not_found(mocker):
    """職務経歴書が未登録の場合に422が返ること"""
    mocker.patch(
        "src.api.resume.firestore_manager.get_resume_job_analysis",
        return_value=SAMPLE_JOB_ANALYSIS,
    )
    mocker.patch(
        "src.api.resume.firestore_manager.get_resume_profile",
        return_value=None,
    )
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/resume/jobs/abc123/company-questions",
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 422


async def test_get_company_questions_success(mocker):
    """保存済みの逆質問リストを正常に取得できること"""
    job_with_questions = SAMPLE_JOB_ANALYSIS.model_copy(
        update={"company_facing_questions": SAMPLE_COMPANY_QUESTIONS.items}
    )
    mocker.patch(
        "src.api.resume.firestore_manager.get_resume_job_analysis",
        return_value=job_with_questions,
    )
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.get(
            "/resume/jobs/abc123/company-questions",
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "question" in data[0]
    assert "intent" in data[0]
    assert "talking_point" in data[0]


async def test_get_company_questions_not_generated(mocker):
    """逆質問未生成の場合に404が返ること"""
    mocker.patch(
        "src.api.resume.firestore_manager.get_resume_job_analysis",
        return_value=SAMPLE_JOB_ANALYSIS,
    )
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.get(
            "/resume/jobs/abc123/company-questions",
            headers={"X-API-KEY": "test-key"},
        )

    assert response.status_code == 404
