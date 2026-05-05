import asyncio
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
    CompanyProfile,
    ExperienceMatchList,
    PersonalProfile,
    ResumeGapAnalysisResult,
    ResumeInterviewQuestionList,
    ResumeJobAnalysisResult,
    ResumeProfile,
    _CompanyInfoSummary,
    _CompanyPdfExtract,
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


async def _fetch_url_text(url: str) -> str | None:
    """URLのHTMLを取得してテキストを抽出する。失敗時はNoneを返す。"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", response.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text if len(text) >= 100 else None
    except Exception:
        return None


def _build_company_aggregation_prompt(sources: dict[str, str]) -> str:
    sections = "\n\n".join(f"### {label}\n{content}" for label, content in sources.items())
    return (
        "以下の複数の情報ソースから、この企業の「企業統合プロフィール」を日本語で作成してください。\n\n"
        "## 統合指示\n"
        "以下の観点で情報を統合・整理してください：\n"
        "1. 企業のミッション・ビジョン・バリュー\n"
        "2. 事業内容・プロダクト・サービス\n"
        "3. 技術スタック・エンジニアリング文化（情報がある場合）\n"
        "4. 求める人物像・カルチャーフィット\n"
        "5. 働き方・職場環境・福利厚生\n"
        "6. 社員の声・実際の雰囲気（インタビューがある場合）\n\n"
        "重複情報は統合し、矛盾がある場合は両方を記載してください。\n"
        "company_nameには情報から特定した企業名を入れてください（不明な場合は「不明」）。\n\n"
        f"## 情報ソース\n\n{sections}"
    )


def _build_matching_prompt(
    job_company: str,
    job_role: str,
    job_skills: list[str],
    job_desired: str,
    job_culture: str,
    profile: ResumeProfile,
    personal: PersonalProfile | None = None,
    company_info: str | None = None,
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
    company_info_section = (
        f"\n## 企業の詳細情報（採用ページ・技術ブログ等より）\n{company_info[:2000]}\n"
        if company_info
        else ""
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
        f"企業文化: {job_culture}\n"
        + company_info_section
        + "\n求人との関連性が高いスキル・経験を5件選び、具体的な活用シーンと"
        "面接でアピールすべき優先度（1〜5、1が最重要）を付けてください。"
    )


def _build_questions_prompt(
    job_company: str,
    job_role: str,
    profile: ResumeProfile,
    matches: list,
    personal: PersonalProfile | None = None,
    company_info: str | None = None,
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
    company_info_section = (
        f"\n## 企業の詳細情報（採用ページ・技術ブログ等より）\n{company_info[:2000]}\n"
        if company_info
        else ""
    )
    return (
        "あなたは経験豊富な面接コーチです。\n"
        "以下の求人と職務経歴のマッチング結果をもとに、"
        "この企業の面接で実際に聞かれそうな質問を5〜8件生成してください。\n"
        "各質問に対し、求職者の具体的な職務経歴・実績を活かしたSTAR形式の"
        "回答例（200字以上）を作成してください。\n\n"
        f"## 求職者サマリー\n{profile.summary}\n"
        + personal_section
        + f"\n## 求人\n企業: {job_company} / 役職: {job_role}\n"
        + company_info_section
        + f"\n## スキル・経験のマッチング\n{match_summary}\n\n"
        "## 注意事項\n"
        "- 行動面接質問（「〜した経験を教えてください」形式）を優先してください\n"
        "- 具体的な実績・数字を盛り込んだ回答例にしてください\n"
        "- 企業の詳細情報がある場合は企業文化・技術スタックを質問・回答に反映させてください\n"
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
    company_info: str | None = None,
) -> str:
    match_summary = "\n".join(
        f"- {m.skill_or_experience}: {m.relevance_reason}" for m in matches
    )
    personal_section = ""
    if personal and personal.career_vision:
        personal_section = f"\n## 求職者のキャリアビジョン\n{personal.career_vision}\n"
    company_info_section = (
        f"\n## 企業の詳細情報（採用ページ・技術ブログ等より）\n{company_info[:2000]}\n"
        if company_info
        else ""
    )
    return (
        "求職者の職務経歴と求人要件を比較し、ギャップ分析を行ってください。\n\n"
        f"## 求職者スキル\n{', '.join(profile.skills)}\n\n"
        f"## 職務経歴サマリー\n{profile.summary}\n"
        + personal_section
        + f"\n## 求人必須スキル\n{', '.join(job_skills)}\n\n"
        f"## 求人の求める人物像\n{job_desired}\n"
        + company_info_section
        + f"\n## マッチしたスキル・経験\n{match_summary}\n\n"
        "## 指示\n"
        "1. gap_analysis（300字以上）: 職務経歴で補完できる要件と補完が難しいギャップ、"
        "そのギャップへの具体的な対策・アピール方法を詳しく記述してください\n"
        "2. overall_fit_score（0.0〜1.0）: "
        "スキルの適合度・経験年数・文化フィットを総合判断したスコア"
    )


# --- パイプライン ---


async def _run_pipeline(
    raw_text: str,
    profile: ResumeProfile,
    personal: PersonalProfile | None = None,
    company_info: str | None = None,
    company_profile_id: str | None = None,
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
            job.desired_person, job.culture, profile, personal, company_info,
        ),
        response_schema=ExperienceMatchList,
    )

    # Step 3: 想定面接質問と回答例の生成
    question_list = await _ai_core.analyze_text(
        prompt=_build_questions_prompt(
            job.company_name, job.role, profile, match_list.items, personal, company_info
        ),
        response_schema=ResumeInterviewQuestionList,
    )

    # Step 4: ギャップ分析とフィットスコア算出
    gap_result = await _ai_core.analyze_text(
        prompt=_build_gap_prompt(
            job.company_name, job.role, job.required_skills,
            job.desired_person, profile, match_list.items, personal, company_info,
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
        company_profile_id=company_profile_id,
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
    company_profile_id: Annotated[
        str | None,
        Form(description="使用する企業プロフィールID（任意）"),
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

    company_info: str | None = None
    if company_profile_id:
        company = await firestore_manager.get_company_profile(company_profile_id)
        if company and company.combined_company_info:
            company_info = company.combined_company_info

    result = await _run_pipeline(raw_text, profile, personal, company_info, company_profile_id)
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


@router.post(
    "/company-profiles", response_model=CompanyProfile, status_code=status.HTTP_201_CREATED
)
async def create_company_profile(
    api_key: Annotated[str, Security(verify_api_key)],
    company_name: Annotated[
        str | None, Form(description="企業名（省略可・AIが情報から推定）")
    ] = None,
    hiring_page_url: Annotated[
        str | None, Form(description="採用ページURL")
    ] = None,
    tech_blog_urls_text: Annotated[
        str | None, Form(description="技術ブログURL（1行1つ）")
    ] = None,
    employee_interview_urls_text: Annotated[
        str | None, Form(description="社員インタビューURL（1行1つ）")
    ] = None,
    free_text: Annotated[
        str | None, Form(description="その他フリーテキスト（会社説明会メモ等）")
    ] = None,
    pdf_files: Annotated[
        list[UploadFile] | None, File(description="企業説明PDFファイル（複数可）")
    ] = None,
) -> CompanyProfile:
    """複数ソースから企業情報を収集・統合し、企業プロフィールとしてFirestoreに保存する"""
    tech_blog_urls = [u.strip() for u in (tech_blog_urls_text or "").splitlines() if u.strip()]
    employee_interview_urls = [
        u.strip() for u in (employee_interview_urls_text or "").splitlines() if u.strip()
    ]
    pdf_files = pdf_files or []

    has_any_source = any([
        hiring_page_url, tech_blog_urls, employee_interview_urls, free_text, pdf_files
    ])
    if not has_any_source:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="情報源を1つ以上指定してください（URL・テキスト・PDFのいずれか）。",
        )

    # URLを並列フェッチ
    all_urls: list[tuple[str, str]] = []
    if hiring_page_url:
        all_urls.append(("採用ページ", hiring_page_url))
    for i, url in enumerate(tech_blog_urls, 1):
        all_urls.append((f"技術ブログ {i}", url))
    for i, url in enumerate(employee_interview_urls, 1):
        all_urls.append((f"社員インタビュー {i}", url))

    sources: dict[str, str] = {}
    if all_urls:
        fetch_results = await asyncio.gather(
            *[_fetch_url_text(url) for _, url in all_urls], return_exceptions=True
        )
        for (label, _), result in zip(all_urls, fetch_results, strict=False):
            if isinstance(result, str) and result:
                sources[label] = result[:3000]

    # PDFを処理
    pdf_gcs_uris: list[str] = []
    if pdf_files:
        upload_root = Path("upload")
        upload_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
            for i, pdf_file in enumerate(pdf_files, 1):
                tmp_path = Path(tmp_dir) / (pdf_file.filename or f"company_{i}.pdf")
                with tmp_path.open("wb") as buf:
                    shutil.copyfileobj(pdf_file.file, buf)
                storage = CloudStorageManager()
                gcs_uri = await storage.upload_file_async(str(tmp_path))
                pdf_gcs_uris.append(gcs_uri)
                try:
                    extracted = await _ai_core.analyze_image(
                        prompt=(
                            "この企業資料のすべての内容を詳細に抽出してください。"
                            "企業名・事業内容・文化・技術・価値観など全情報を含めてください。"
                        ),
                        gcs_uri=gcs_uri,
                        response_schema=_CompanyPdfExtract,
                        mime_type="application/pdf",
                    )
                    if extracted.content:
                        sources[f"企業PDF資料 {i}"] = extracted.content[:3000]
                except Exception:
                    pass

    if free_text and free_text.strip():
        sources["フリーテキスト"] = free_text.strip()[:3000]

    if not sources:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "情報を取得できませんでした。URLが正しいか確認するか、"
                "テキストを直接入力してください。"
            ),
        )

    summary = await _ai_core.analyze_text(
        prompt=_build_company_aggregation_prompt(sources),
        response_schema=_CompanyInfoSummary,
    )

    profile = CompanyProfile(
        company_id=uuid.uuid4().hex,
        company_name=company_name or (
            summary.company_name if summary.company_name != "不明" else None
        ),
        hiring_page_url=hiring_page_url,
        tech_blog_urls=tech_blog_urls,
        employee_interview_urls=employee_interview_urls,
        free_text=free_text,
        pdf_gcs_uris=pdf_gcs_uris,
        combined_company_info=summary.combined_company_info,
        created_at=datetime.now(UTC).isoformat(),
    )
    await firestore_manager.save_company_profile(profile)
    return profile


@router.get("/company-profiles", response_model=list[CompanyProfile])
async def list_company_profiles(
    api_key: Annotated[str, Security(verify_api_key)],
) -> list[CompanyProfile]:
    """登録済みの企業プロフィール一覧を作成日時の降順で返す"""
    return await firestore_manager.list_company_profiles()


@router.get("/company-profiles/{company_id}", response_model=CompanyProfile)
async def get_company_profile(
    company_id: str,
    api_key: Annotated[str, Security(verify_api_key)],
) -> CompanyProfile:
    """指定した company_id の企業プロフィールを返す"""
    profile = await firestore_manager.get_company_profile(company_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"company_id '{company_id}' が見つかりません。",
        )
    return profile


@router.patch("/company-profiles/{company_id}", response_model=CompanyProfile)
async def update_company_profile(
    company_id: str,
    api_key: Annotated[str, Security(verify_api_key)],
    company_name: Annotated[
        str | None, Form(description="企業名（省略可・AIが推定）")
    ] = None,
    hiring_page_url: Annotated[
        str | None, Form(description="採用ページURL")
    ] = None,
    tech_blog_urls_text: Annotated[
        str | None, Form(description="技術ブログURL（1行1つ）")
    ] = None,
    employee_interview_urls_text: Annotated[
        str | None, Form(description="社員インタビューURL（1行1つ）")
    ] = None,
    free_text: Annotated[
        str | None, Form(description="その他フリーテキスト")
    ] = None,
    pdf_files: Annotated[
        list[UploadFile] | None, File(description="企業説明PDF（複数可・送信すると差し替え）")
    ] = None,
) -> CompanyProfile:
    """企業プロフィールのソースを更新してAI統合をやり直す。PDFを送らない場合は既存PDFを維持する。"""
    existing = await firestore_manager.get_company_profile(company_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"company_id '{company_id}' が見つかりません。",
        )

    tech_blog_urls = [u.strip() for u in (tech_blog_urls_text or "").splitlines() if u.strip()]
    employee_interview_urls = [
        u.strip() for u in (employee_interview_urls_text or "").splitlines() if u.strip()
    ]
    pdf_files = pdf_files or []

    # URLを並列フェッチ
    all_urls: list[tuple[str, str]] = []
    if hiring_page_url:
        all_urls.append(("採用ページ", hiring_page_url))
    for i, url in enumerate(tech_blog_urls, 1):
        all_urls.append((f"技術ブログ {i}", url))
    for i, url in enumerate(employee_interview_urls, 1):
        all_urls.append((f"社員インタビュー {i}", url))

    sources: dict[str, str] = {}
    if all_urls:
        fetch_results = await asyncio.gather(
            *[_fetch_url_text(url) for _, url in all_urls], return_exceptions=True
        )
        for (label, _), result in zip(all_urls, fetch_results, strict=False):
            if isinstance(result, str) and result:
                sources[label] = result[:3000]

    # PDFを処理（新規アップロードがあれば差し替え、なければ既存情報を引き継ぐ）
    if pdf_files:
        pdf_gcs_uris: list[str] = []
        upload_root = Path("upload")
        upload_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=upload_root) as tmp_dir:
            for i, pdf_file in enumerate(pdf_files, 1):
                tmp_path = Path(tmp_dir) / (pdf_file.filename or f"company_{i}.pdf")
                with tmp_path.open("wb") as buf:
                    shutil.copyfileobj(pdf_file.file, buf)
                storage = CloudStorageManager()
                gcs_uri = await storage.upload_file_async(str(tmp_path))
                pdf_gcs_uris.append(gcs_uri)
                try:
                    extracted = await _ai_core.analyze_image(
                        prompt=(
                            "この企業資料のすべての内容を詳細に抽出してください。"
                            "企業名・事業内容・文化・技術・価値観など全情報を含めてください。"
                        ),
                        gcs_uri=gcs_uri,
                        response_schema=_CompanyPdfExtract,
                        mime_type="application/pdf",
                    )
                    if extracted.content:
                        sources[f"企業PDF資料 {i}"] = extracted.content[:3000]
                except Exception:
                    pass
    else:
        # 既存PDFを維持し、既存の統合情報をソースの一つとして引き継ぐ
        pdf_gcs_uris = existing.pdf_gcs_uris
        if existing.combined_company_info:
            sources["既存の統合企業情報"] = existing.combined_company_info[:3000]

    if free_text and free_text.strip():
        sources["フリーテキスト"] = free_text.strip()[:3000]

    if not sources:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="情報源が空です。URLまたはテキストを入力してください。",
        )

    summary = await _ai_core.analyze_text(
        prompt=_build_company_aggregation_prompt(sources),
        response_schema=_CompanyInfoSummary,
    )

    updated = CompanyProfile(
        company_id=company_id,
        company_name=company_name or (
            summary.company_name if summary.company_name != "不明" else existing.company_name
        ),
        hiring_page_url=hiring_page_url,
        tech_blog_urls=tech_blog_urls,
        employee_interview_urls=employee_interview_urls,
        free_text=free_text,
        pdf_gcs_uris=pdf_gcs_uris,
        combined_company_info=summary.combined_company_info,
        created_at=existing.created_at,
    )
    await firestore_manager.save_company_profile(updated)
    return updated


@router.delete("/company-profiles/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_profile(
    company_id: str,
    api_key: Annotated[str, Security(verify_api_key)],
) -> None:
    """指定した company_id の企業プロフィールを削除する"""
    existing = await firestore_manager.get_company_profile(company_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"company_id '{company_id}' が見つかりません。",
        )
    await firestore_manager.delete_company_profile(company_id)
