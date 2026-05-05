import re
import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Security, UploadFile, status

from src.api.auth import verify_api_key
from src.core.ai import GeminiCore
from src.core.firestore import firestore_manager
from src.core.resume_schema import (
    ExperienceMatchList,
    PersonalProfile,
    ResumeGapAnalysisResult,
    ResumeInterviewQuestionList,
    ResumeJobAnalysisResult,
    ResumeProfile,
    _ResumeProfileExtract,
)
from src.core.storage import CloudStorageManager
from src.core.strengths_schema import _JobPostingExtract

router = APIRouter(prefix="/resume", tags=["resume"])
_ai_core = GeminiCore()


# --- プロンプトビルダー ---


def _build_resume_extraction_prompt(gcs_uri: str) -> str:
    return (
        "添付のPDFは職務経歴書です。以下の情報を構造化して抽出してください。\n\n"
        "## 抽出指示\n"
        "- skills: 保有スキル・技術・資格をすべてリストアップしてください\n"
        "- work_experiences: 職歴を新しい順に並べてください。各職歴には会社名・役職・在籍期間・"
        "担当業務・主な実績を含めてください\n"
        "- summary: キャリア全体のサマリーを200字以上で記述してください。"
        "専門領域・強み・キャリアの方向性を含めること\n\n"
        f"source_gcs_uriは '{gcs_uri}' を使用してください。"
    )


def _build_job_extraction_prompt(raw_text: str) -> str:
    return (
        "以下の求人情報テキストを解析し、構造化データとして抽出してください。\n\n"
        "## 抽出指示\n"
        "- company_name: 企業名を正確に抽出してください\n"
        "- role: 職種・ポジション名を抽出してください\n"
        "- required_skills: 必須・歓迎スキルを個別の文字列リストとして抽出してください\n"
        "- desired_person: 求める人物像・マインドセット・"
        "カルチャーフィットの記述を統合してください\n"
        "- culture: 会社の文化・働き方・環境に関する記述をまとめてください\n\n"
        f"## 求人情報\n{raw_text}"
    )


def _build_matching_prompt(
    job_company: str,
    job_role: str,
    job_skills: list[str],
    job_desired: str,
    job_culture: str,
    profile: ResumeProfile,
    personal: PersonalProfile | None = None,
) -> str:
    skills_summary = "、".join(profile.skills)
    exp_summary = "\n".join(
        f"- {e.company}（{e.role}、{e.period}）: {e.description}" for e in profile.work_experiences
    )
    personal_section = ""
    if personal and (personal.values or personal.career_vision):
        values_str = "、".join(personal.values) if personal.values else "（未設定）"
        personal_section = (
            f"\n## 求職者のパーソナリティ\n"
            f"価値観: {values_str}\n"
            f"キャリアビジョン: {personal.career_vision}\n"
        )
    return (
        "あなたはキャリアコンサルタントです。求職者の職務経歴と求人要件を照合し、"
        "各スキル・経験が求人にどう活かせるかを具体的に分析してください。\n\n"
        f"## 求職者のスキル\n{skills_summary}\n\n"
        f"## 職歴\n{exp_summary}\n"
        + personal_section
        + "\n## 求人情報\n"
        f"企業: {job_company}\n"
        f"役職: {job_role}\n"
        f"必須スキル: {', '.join(job_skills)}\n"
        f"求める人物像: {job_desired}\n"
        f"企業文化: {job_culture}\n\n"
        "求人との関連性が高いスキル・経験を5件選び、具体的な活用シーンと"
        "面接でアピールすべき優先度（1〜5、1が最重要）を付けてください。"
    )


def _build_questions_prompt(
    job_company: str,
    job_role: str,
    profile: ResumeProfile,
    matches: list,
    personal: PersonalProfile | None = None,
) -> str:
    match_summary = "\n".join(
        f"- {m.skill_or_experience}（優先度{m.priority}）: {m.relevance_reason}"
        for m in sorted(matches, key=lambda x: x.priority)
    )
    personal_section = ""
    if personal:
        values_str = "、".join(personal.values) if personal.values else "（未設定）"
        items_str = (
            "、".join(personal.influential_items) if personal.influential_items else "（未設定）"
        )
        personal_section = (
            f"\n## 求職者のパーソナリティ\n"
            f"価値観: {values_str}\n"
            f"影響を受けた本・人: {items_str}\n"
            f"キャリアビジョン: {personal.career_vision}\n"
            f"働き方の好み: {personal.work_style}\n"
        )
        if personal.episodes:
            episodes_str = "\n".join(
                f"  【{ep.title}】 S:{ep.situation} / T:{ep.task} / A:{ep.action} / R:{ep.result}"
                for ep in personal.episodes
            )
            personal_section += f"\n印象的なエピソード（STAR形式）:\n{episodes_str}\n"
    return (
        "あなたは経験豊富な面接コーチです。\n"
        "以下の求人と職務経歴のマッチング結果をもとに、"
        "この企業の面接で実際に聞かれそうな質問を5〜8件生成してください。\n"
        "各質問に対し、求職者の具体的な職務経歴・実績を活かしたSTAR形式の"
        "回答例（200字以上）を作成してください。\n\n"
        f"## 求職者サマリー\n{profile.summary}\n"
        + personal_section
        + f"\n## 求人\n企業: {job_company} / 役職: {job_role}\n\n"
        f"## スキル・経験のマッチング\n{match_summary}\n\n"
        "## 注意事項\n"
        "- 行動面接質問（「〜した経験を教えてください」形式）を優先してください\n"
        "- 具体的な実績・数字を盛り込んだ回答例にしてください\n"
        "- パーソナルプロフィールがある場合は価値観・エピソードを回答例に自然に反映させてください\n"
        "- experience_usedには実際に回答で言及した職歴・スキルの名称のみ含めてください"
    )


def _build_gap_prompt(
    job_company: str,
    job_role: str,
    job_skills: list[str],
    job_desired: str,
    profile: ResumeProfile,
    matches: list,
    personal: PersonalProfile | None = None,
) -> str:
    match_summary = "\n".join(
        f"- {m.skill_or_experience}: {m.relevance_reason}" for m in matches
    )
    personal_section = ""
    if personal and personal.career_vision:
        personal_section = f"\n## 求職者のキャリアビジョン\n{personal.career_vision}\n"
    return (
        "求職者の職務経歴と求人要件を比較し、ギャップ分析を行ってください。\n\n"
        f"## 求職者スキル\n{', '.join(profile.skills)}\n\n"
        f"## 職務経歴サマリー\n{profile.summary}\n"
        + personal_section
        + f"\n## 求人必須スキル\n{', '.join(job_skills)}\n\n"
        f"## 求人の求める人物像\n{job_desired}\n\n"
        f"## マッチしたスキル・経験\n{match_summary}\n\n"
        "## 指示\n"
        "1. gap_analysis（300字以上）: 職務経歴で補完できる要件と補完が難しいギャップ、"
        "そのギャップへの具体的な対策・アピール方法を詳しく記述してください\n"
        "2. overall_fit_score（0.0〜1.0）: "
        "スキルの適合度・経験年数・文化フィットを総合判断したスコア"
    )


# --- パイプライン ---


async def _run_pipeline(
    raw_text: str, profile: ResumeProfile, personal: PersonalProfile | None = None
) -> ResumeJobAnalysisResult:
    # Step 1: 求人情報の構造化抽出
    job = await _ai_core.analyze_text(
        prompt=_build_job_extraction_prompt(raw_text),
        response_schema=_JobPostingExtract,
    )

    # Step 2: スキル・経験のマッチング分析
    match_list = await _ai_core.analyze_text(
        prompt=_build_matching_prompt(
            job.company_name, job.role, job.required_skills,
            job.desired_person, job.culture, profile, personal,
        ),
        response_schema=ExperienceMatchList,
    )

    # Step 3: 想定面接質問と回答例の生成
    question_list = await _ai_core.analyze_text(
        prompt=_build_questions_prompt(
            job.company_name, job.role, profile, match_list.items, personal
        ),
        response_schema=ResumeInterviewQuestionList,
    )

    # Step 4: ギャップ分析とフィットスコア算出
    gap_result = await _ai_core.analyze_text(
        prompt=_build_gap_prompt(
            job.company_name, job.role, job.required_skills,
            job.desired_person, profile, match_list.items, personal,
        ),
        response_schema=ResumeGapAnalysisResult,
    )

    return ResumeJobAnalysisResult(
        job_id=uuid.uuid4().hex,
        job_posting_company=job.company_name,
        job_posting_role=job.role,
        job_posting_required_skills=job.required_skills,
        job_posting_desired_person=job.desired_person,
        job_posting_culture=job.culture,
        job_posting_raw_text=raw_text,
        experience_matches=match_list.items,
        interview_questions=question_list.items,
        gap_analysis=gap_result.gap_analysis,
        overall_fit_score=gap_result.overall_fit_score,
        created_at=datetime.now(UTC).isoformat(),
    )


# --- エンドポイント ---


@router.post("/profile", response_model=ResumeProfile, status_code=status.HTTP_201_CREATED)
async def upload_resume_profile(
    file: Annotated[UploadFile, File(description="職務経歴書PDFファイル")],
    api_key: Annotated[str, Security(verify_api_key)],
) -> ResumeProfile:
    """職務経歴書PDFをアップロードし、構造化プロフィールを抽出してFirestoreに保存する"""
    upload_root = Path("upload")
    upload_root.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
        tmp_path = Path(tmp_dir) / (file.filename or "resume.pdf")
        with tmp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        storage = CloudStorageManager()
        gcs_uri = await storage.upload_file_async(str(tmp_path))

        try:
            extracted = await _ai_core.analyze_image(
                prompt=_build_resume_extraction_prompt(gcs_uri),
                gcs_uri=gcs_uri,
                response_schema=_ResumeProfileExtract,
                mime_type="application/pdf",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF解析に失敗しました: {e}",
            ) from e

    profile = ResumeProfile(**extracted.model_dump(), raw_text="", source_gcs_uri=gcs_uri)
    await firestore_manager.save_resume_profile(profile)
    return profile


@router.get("/profile", response_model=ResumeProfile)
async def get_resume_profile(
    api_key: Annotated[str, Security(verify_api_key)],
) -> ResumeProfile:
    """Firestoreに保存済みの職務経歴書プロフィールを取得する"""
    profile = await firestore_manager.get_resume_profile()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "職務経歴書がまだ登録されていません。"
                "POST /resume/profile でPDFをアップロードしてください。"
            ),
        )
    return profile


@router.post(
    "/personal-profile", response_model=PersonalProfile, status_code=status.HTTP_201_CREATED
)
async def upsert_personal_profile(
    profile: PersonalProfile,
    api_key: Annotated[str, Security(verify_api_key)],
) -> PersonalProfile:
    """パーソナルプロフィール（価値観・エピソード等）を登録・更新してFirestoreに保存する"""
    await firestore_manager.save_personal_profile(profile)
    return profile


@router.get("/personal-profile", response_model=PersonalProfile)
async def get_personal_profile(
    api_key: Annotated[str, Security(verify_api_key)],
) -> PersonalProfile:
    """Firestoreに保存済みのパーソナルプロフィールを取得する"""
    profile = await firestore_manager.get_personal_profile()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="パーソナルプロフィールが未登録です。",
        )
    return profile


@router.post("/jobs", response_model=ResumeJobAnalysisResult, status_code=status.HTTP_201_CREATED)
async def create_resume_job_analysis(
    api_key: Annotated[str, Security(verify_api_key)],
    url: Annotated[
        str | None,
        Form(description="求人ページのURL（urlまたはtextのどちらか必須）"),
    ] = None,
    text: Annotated[
        str | None,
        Form(description="求人情報のテキスト（urlまたはtextのどちらか必須）"),
    ] = None,
) -> ResumeJobAnalysisResult:
    """求人URLまたはテキストを受け取り、職務経歴書との適合度を分析してFirestoreに保存する"""
    if not url and not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="urlまたはtextのどちらかを指定してください。",
        )

    profile = await firestore_manager.get_resume_profile()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "職務経歴書が未登録です。"
                "先に POST /resume/profile でPDFをアップロードしてください。"
            ),
        )

    if url:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                raw_text = response.text
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"求人ページの取得に失敗しました（HTTP {e.response.status_code}）: {url}",
            ) from e
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"求人ページへの接続に失敗しました: {e}",
            ) from e

        visible_text = re.sub(r"<[^>]+>", " ", raw_text)
        visible_text = re.sub(r"\s+", " ", visible_text).strip()
        if len(visible_text) < 200:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "このサイトでは求人情報を取得できませんでした。"
                    "JavaScriptで描画されるページ、またはログインが必要なページの可能性があります。"
                    "求人ページのテキストをコピーして「テキスト入力」でお試しください。"
                ),
            )
    else:
        raw_text = text  # type: ignore[assignment]

    personal = await firestore_manager.get_personal_profile()
    result = await _run_pipeline(raw_text, profile, personal)
    await firestore_manager.save_resume_job_analysis(result)
    return result


@router.get("/jobs", response_model=list[ResumeJobAnalysisResult])
async def list_resume_job_analyses(
    api_key: Annotated[str, Security(verify_api_key)],
) -> list[ResumeJobAnalysisResult]:
    """登録済みの全職務経歴書×求人分析結果を作成日時の降順で返す"""
    return await firestore_manager.list_resume_job_analyses()


@router.get("/jobs/{job_id}", response_model=ResumeJobAnalysisResult)
async def get_resume_job_analysis(
    job_id: str,
    api_key: Annotated[str, Security(verify_api_key)],
) -> ResumeJobAnalysisResult:
    """指定した job_id の職務経歴書×求人分析結果を返す"""
    result = await firestore_manager.get_resume_job_analysis(job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"job_id '{job_id}' が見つかりません。",
        )
    return result
