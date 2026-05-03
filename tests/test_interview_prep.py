import json

import pytest
from fastapi import HTTPException

from src.api.jobs import _run_pipeline
from src.core.ai import GeminiCore
from src.core.strengths_schema import (
    GapAnalysisResult,
    InterviewQuestion,
    InterviewQuestionList,
    JobPosting,
    Strength,
    StrengthMatch,
    StrengthMatchList,
    StrengthsProfile,
)

# --- テスト用フィクスチャ ---

SAMPLE_PROFILE = StrengthsProfile(
    top5=[
        Strength(
            name="ポジティブ", english_name="Positivity",
            domain="人間関係構築力", description="前向きで周囲を明るくする",
        ),
        Strength(
            name="適応性", english_name="Adaptability",
            domain="人間関係構築力", description="変化に柔軟に対応する",
        ),
        Strength(
            name="学習欲", english_name="Learner",
            domain="戦略的思考力", description="常に学び向上し続ける",
        ),
        Strength(
            name="収集心", english_name="Input",
            domain="戦略的思考力", description="情報を収集し保管する",
        ),
        Strength(
            name="原点思考", english_name="Context",
            domain="戦略的思考力", description="過去から現在を理解する",
        ),
    ],
    raw_text="サンプルPDFテキスト",
    source_gcs_uri="gs://bucket/strengths.pdf",
)

SAMPLE_JOB_POSTING = JobPosting(
    company_name="テスト株式会社",
    role="バックエンドエンジニア",
    required_skills=["Python", "FastAPI", "SQL"],
    desired_person="自律的に動ける方",
    culture="フラットな組織文化",
    raw_text="求人情報の原文",
)

SAMPLE_MATCH_LIST = StrengthMatchList(
    items=[
        StrengthMatch(
            strength_name="学習欲",
            relevance_reason="新技術への適応が求められる職種に最適",
            priority=1,
        ),
        StrengthMatch(
            strength_name="ポジティブ",
            relevance_reason="チームの雰囲気を高める",
            priority=2,
        ),
    ]
)

SAMPLE_QUESTION_LIST = InterviewQuestionList(
    items=[
        InterviewQuestion(
            question="技術的に困難な問題をどう解決しましたか？",
            answer_example="学習欲を活かして...",
            strengths_used=["学習欲"],
        )
    ]
)

SAMPLE_GAP_RESULT = GapAnalysisResult(
    gap_analysis="強みと求人要件の分析：学習欲と収集心がバックエンド開発の技術習得に直結する。" * 5,
    overall_fit_score=0.82,
)


def _make_mock_response(data: dict, mocker) -> object:
    mock_resp = mocker.MagicMock()
    mock_resp.text = json.dumps(data, ensure_ascii=False)
    return mock_resp


# --- テスト ---


async def test_pipeline_missing_profile(mocker):
    """StrengthsProfileが未登録の場合、422エラーが発生することを確認する"""
    mocker.patch("src.api.jobs.firestore_manager.get_strengths_profile", return_value=None)

    core = GeminiCore(project_id="test-project", location="asia-northeast1")
    mocker.patch.object(
        core.client.aio.models,
        "generate_content",
        new_callable=mocker.AsyncMock,
        return_value=_make_mock_response(SAMPLE_JOB_POSTING.model_dump(), mocker),
    )
    mocker.patch("src.api.jobs._ai_core", core)

    with pytest.raises(HTTPException) as exc_info:
        await _run_pipeline("求人テキスト")

    assert exc_info.value.status_code == 422


async def test_full_pipeline_success(mocker):
    """パイプラインが正常に完了し、JobAnalysisResultが返ることを確認する"""
    # Firestore モック
    mocker.patch(
        "src.api.jobs.firestore_manager.get_strengths_profile", return_value=SAMPLE_PROFILE
    )

    # Gemini への4回の呼び出しをシーケンシャルにモック
    mock_responses = [
        _make_mock_response(SAMPLE_JOB_POSTING.model_dump(), mocker),
        _make_mock_response(SAMPLE_MATCH_LIST.model_dump(), mocker),
        _make_mock_response(SAMPLE_QUESTION_LIST.model_dump(), mocker),
        _make_mock_response(SAMPLE_GAP_RESULT.model_dump(), mocker),
    ]

    core = GeminiCore(project_id="test-project", location="asia-northeast1")
    mocker.patch.object(
        core.client.aio.models,
        "generate_content",
        new_callable=mocker.AsyncMock,
        side_effect=mock_responses,
    )
    mocker.patch("src.api.jobs._ai_core", core)

    result = await _run_pipeline("求人テキスト")

    assert result.job_id != ""
    assert result.job_posting.company_name == "テスト株式会社"
    assert len(result.strength_matches) == 2
    assert len(result.interview_questions) == 1
    assert result.overall_fit_score == pytest.approx(0.82)
    assert result.created_at != ""


async def test_get_strengths_profile_not_found(mocker):
    """プロフィール未登録時にGET /strengths/profileが404を返すことを確認する"""
    from fastapi.testclient import TestClient

    mocker.patch("src.api.strengths.firestore_manager.get_strengths_profile", return_value=None)
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.get("/strengths/profile", headers={"X-API-KEY": "test-key"})

    assert response.status_code == 404


async def test_get_job_analysis_not_found(mocker):
    """存在しないjob_idでGET /jobs/{job_id}が404を返すことを確認する"""
    from fastapi.testclient import TestClient

    mocker.patch("src.api.jobs.firestore_manager.get_job_analysis", return_value=None)
    mocker.patch("src.core.config.settings.internal_api_key", "test-key")

    from src.api.main import app

    with TestClient(app) as client:
        response = client.get("/jobs/nonexistent-id", headers={"X-API-KEY": "test-key"})

    assert response.status_code == 404
