from google.cloud import firestore

from src.core.config import settings
from src.core.resume_schema import ResumeJobAnalysisResult, ResumeProfile
from src.core.strengths_schema import JobAnalysisResult, StrengthsProfile

_COLLECTION_PROFILE = "strengths_profiles"
_COLLECTION_JOBS = "job_analyses"
_COLLECTION_RESUME_PROFILE = "resume_profiles"
_COLLECTION_RESUME_JOBS = "resume_job_analyses"
_PROFILE_DOC_ID = "current"


class FirestoreManager:
    def __init__(self) -> None:
        self.client: firestore.AsyncClient = firestore.AsyncClient(
            project=settings.google_cloud_project,
            database=settings.firestore_database,
        )

    async def save_strengths_profile(self, profile: StrengthsProfile) -> str:
        doc_ref = self.client.collection(_COLLECTION_PROFILE).document(_PROFILE_DOC_ID)
        await doc_ref.set(profile.model_dump())
        return _PROFILE_DOC_ID

    async def get_strengths_profile(self) -> StrengthsProfile | None:
        doc_ref = self.client.collection(_COLLECTION_PROFILE).document(_PROFILE_DOC_ID)
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            return None
        return StrengthsProfile.model_validate(snapshot.to_dict())

    async def save_job_analysis(self, result: JobAnalysisResult) -> str:
        doc_ref = self.client.collection(_COLLECTION_JOBS).document(result.job_id)
        await doc_ref.set(result.model_dump())
        return result.job_id

    async def get_job_analysis(self, job_id: str) -> JobAnalysisResult | None:
        doc_ref = self.client.collection(_COLLECTION_JOBS).document(job_id)
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            return None
        return JobAnalysisResult.model_validate(snapshot.to_dict())

    async def list_job_analyses(self) -> list[JobAnalysisResult]:
        query = self.client.collection(_COLLECTION_JOBS).order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )
        results: list[JobAnalysisResult] = []
        async for doc in query.stream():
            results.append(JobAnalysisResult.model_validate(doc.to_dict()))
        return results

    async def save_resume_profile(self, profile: ResumeProfile) -> str:
        doc_ref = self.client.collection(_COLLECTION_RESUME_PROFILE).document(_PROFILE_DOC_ID)
        await doc_ref.set(profile.model_dump())
        return _PROFILE_DOC_ID

    async def get_resume_profile(self) -> ResumeProfile | None:
        doc_ref = self.client.collection(_COLLECTION_RESUME_PROFILE).document(_PROFILE_DOC_ID)
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            return None
        return ResumeProfile.model_validate(snapshot.to_dict())

    async def save_resume_job_analysis(self, result: ResumeJobAnalysisResult) -> str:
        doc_ref = self.client.collection(_COLLECTION_RESUME_JOBS).document(result.job_id)
        await doc_ref.set(result.model_dump())
        return result.job_id

    async def get_resume_job_analysis(self, job_id: str) -> ResumeJobAnalysisResult | None:
        doc_ref = self.client.collection(_COLLECTION_RESUME_JOBS).document(job_id)
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            return None
        return ResumeJobAnalysisResult.model_validate(snapshot.to_dict())

    async def list_resume_job_analyses(self) -> list[ResumeJobAnalysisResult]:
        query = self.client.collection(_COLLECTION_RESUME_JOBS).order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )
        results: list[ResumeJobAnalysisResult] = []
        async for doc in query.stream():
            results.append(ResumeJobAnalysisResult.model_validate(doc.to_dict()))
        return results


firestore_manager = FirestoreManager()
