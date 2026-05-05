import uuid
from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Form, HTTPException, Security, status

from src.api.auth import verify_api_key
from src.core.ai import GeminiCore
from src.core.firestore import firestore_manager
from src.core.strengths_schema import (
    GapAnalysisResult,
    InterviewQuestionList,
    JobAnalysisResult,
    JobPosting,
    StrengthMatch,
    StrengthMatchList,
    StrengthsProfile,
    _JobPostingExtract,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])
_ai_core = GeminiCore()


# --- プロンプトビルダー ---


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


def _build_matching_prompt(job: JobPosting, profile: StrengthsProfile) -> str:
    strengths_summary = "\n".join(
        f"- {s.name} ({s.english_name}, {s.domain}): {s.description}" for s in profile.top5
    )
    return (
        "あなたはキャリアコーチです。求職者の強みと求人要件を照合し、"
        "各強みが求人にどう活かせるかを具体的に分析してください。\n\n"
        f"## 求職者の強み（Top 5）\n{strengths_summary}\n\n"
        "## 求人情報\n"
        f"企業: {job.company_name}\n"
        f"役職: {job.role}\n"
        f"必須スキル: {', '.join(job.required_skills)}\n"
        f"求める人物像: {job.desired_person}\n"
        f"企業文化: {job.culture}\n\n"
        "各強みについて、求人との関連性と具体的な活用シーンを説明し、"
        "面接でアピールすべき優先度（1〜5、1が最重要）を付けてください。"
        "全5つの強みを必ずリストに含めてください。"
    )


def _build_questions_prompt(
    job: JobPosting,
    profile: StrengthsProfile,
    matches: list[StrengthMatch],
) -> str:
    match_summary = "\n".join(
        f"- {m.strength_name}（優先度{m.priority}）: {m.relevance_reason}"
        for m in sorted(matches, key=lambda x: x.priority)
    )
    strengths_names = "、".join(s.name for s in profile.top5)
    return (
        "あなたは経験豊富な面接コーチです。\n"
        "以下の求人と強みのマッチング結果をもとに、"
        "この企業の面接で実際に聞かれそうな質問を5〜8件生成してください。\n"
        "各質問に対し、求職者の強みを活かしたSTAR形式の"
        "具体的な回答例（200字以上）を作成してください。\n\n"
        f"## 求職者の強み（Top 5）\n{strengths_names}\n\n"
        f"## 求人\n企業: {job.company_name} / 役職: {job.role}\n\n"
        f"## 強みのマッチング\n{match_summary}\n\n"
        "## 注意事項\n"
        "- 行動面接質問（「〜した経験を教えてください」形式）を優先してください\n"
        "- 強みを自然に盛り込んだ回答例にしてください\n"
        "- strengths_usedには実際に回答で言及した強みの名前のみ含めてください"
    )


def _build_gap_prompt(
    job: JobPosting,
    profile: StrengthsProfile,
    matches: list[StrengthMatch],
) -> str:
    match_summary = "\n".join(f"- {m.strength_name}: {m.relevance_reason}" for m in matches)
    strengths_names = "、".join(s.name for s in profile.top5)
    return (
        "求職者の強みプロファイルと求人要件を比較し、ギャップ分析を行ってください。\n\n"
        f"## 求職者の強み（Top 5）\n{strengths_names}\n\n"
        f"## 求人必須スキル\n{', '.join(job.required_skills)}\n\n"
        f"## 求人の求める人物像\n{job.desired_person}\n\n"
        f"## マッチした強みの分析\n{match_summary}\n\n"
        "## 指示\n"
        "1. gap_analysis（300字以上）: 強みで補完できる要件と補完が難しいギャップ、"
        "そのギャップへの具体的な対策・言い換え方を詳しく記述してください\n"
        "2. overall_fit_score（0.0〜1.0）: "
        "強みの適合度・スキルカバー率・文化フィットを総合判断したスコア"
    )


# --- エージェントパイプライン ---


async def _run_pipeline(raw_text: str) -> JobAnalysisResult:
    """マルチステップエージェントパイプライン"""
    # Step 2: 求人情報の構造化抽出（raw_textはGeminiに出力させず直接セット）
    extracted = await _ai_core.analyze_text(
        prompt=_build_job_extraction_prompt(raw_text),
        response_schema=_JobPostingExtract,
    )
    job_posting = JobPosting(**extracted.model_dump(), raw_text=raw_text)

    # Step 3: StrengthsProfile をFirestoreから読み込み
    profile = await firestore_manager.get_strengths_profile()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "StrengthsProfileが未登録です。"
                "先に POST /strengths/profile でPDFをアップロードしてください。"
            ),
        )

    # Step 4: 強みのマッチング分析
    match_list = await _ai_core.analyze_text(
        prompt=_build_matching_prompt(job_posting, profile),
        response_schema=StrengthMatchList,
    )

    # Step 5: 想定面接質問と回答例の生成
    question_list = await _ai_core.analyze_text(
        prompt=_build_questions_prompt(job_posting, profile, match_list.items),
        response_schema=InterviewQuestionList,
    )

    # Step 6: ギャップ分析とフィットスコア算出
    gap_result = await _ai_core.analyze_text(
        prompt=_build_gap_prompt(job_posting, profile, match_list.items),
        response_schema=GapAnalysisResult,
    )

    return JobAnalysisResult(
        job_id=uuid.uuid4().hex,
        job_posting=job_posting,
        strength_matches=match_list.items,
        interview_questions=question_list.items,
        gap_analysis=gap_result.gap_analysis,
        overall_fit_score=gap_result.overall_fit_score,
        created_at=datetime.now(UTC).isoformat(),
    )


# --- エンドポイント ---


@router.post("", response_model=JobAnalysisResult, status_code=status.HTTP_201_CREATED)
async def create_job_analysis(
    api_key: Annotated[str, Security(verify_api_key)],
    url: Annotated[
        str | None,
        Form(description="求人ページのURL（urlまたはtextのどちらか必須）"),
    ] = None,
    text: Annotated[
        str | None,
        Form(description="求人情報のテキスト（urlまたはtextのどちらか必須）"),
    ] = None,
) -> JobAnalysisResult:
    """求人URLまたはテキストを受け取り、マルチステップエージェントで面接対策を生成してFirestoreに保存する"""
    if not url and not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="urlまたはtextのどちらかを指定してください。",
        )

    # Step 1: URLの場合はテキストを取得
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
    else:
        raw_text = text  # type: ignore[assignment]

    result = await _run_pipeline(raw_text)
    await firestore_manager.save_job_analysis(result)
    return result


@router.get("", response_model=list[JobAnalysisResult])
async def list_job_analyses(
    api_key: Annotated[str, Security(verify_api_key)],
) -> list[JobAnalysisResult]:
    """登録済みの全求人分析結果を作成日時の降順で返す"""
    return await firestore_manager.list_job_analyses()


@router.get("/{job_id}", response_model=JobAnalysisResult)
async def get_job_analysis(
    job_id: str,
    api_key: Annotated[str, Security(verify_api_key)],
) -> JobAnalysisResult:
    """指定した job_id の求人分析結果を返す"""
    result = await firestore_manager.get_job_analysis(job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"job_id '{job_id}' が見つかりません。",
        )
    return result
