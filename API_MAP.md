# API_MAP.md - Existing Endpoints

新しいAPIを追加する前に重複がないか確認すること。

| Method | Path | 概要 | ルーターファイル |
|--------|------|------|----------------|
| POST | /analyze | 画像・テキスト汎用解析 | `src/api/main.py` |
| POST | /analyze-upload | ファイルアップロード＋GCS経由解析 | `src/api/main.py` |
| POST | /analyze-environment | 環境センサーデータ解析 | `src/api/main.py` |
| POST | /anonymize/text | テキスト匿名化（人名・会社名・メール等） | `src/api/anonymize.py` |
| POST | /pdf/extract-text | PDF文字起こし | `src/api/pdf.py` |
| GET  | /pdf/extract-text/{doc_id} | 文字起こし結果取得 | `src/api/pdf.py` |
| POST | /strengths/profile | CliftonStrengths PDFアップロード | `src/api/strengths.py` |
| GET  | /strengths/profile | 強みプロフィール取得 | `src/api/strengths.py` |
| POST | /jobs | 強み×求人マッチング分析 | `src/api/jobs.py` |
| GET  | /jobs | 分析一覧取得 | `src/api/jobs.py` |
| GET  | /jobs/{job_id} | 分析詳細取得 | `src/api/jobs.py` |
| POST | /resume/profile | 履歴書PDFアップロード | `src/api/resume.py` |
| GET  | /resume/profile | 履歴書プロフィール取得 | `src/api/resume.py` |
| POST | /resume/personal-profile | 価値観・ビジョン登録 | `src/api/resume.py` |
| GET  | /resume/personal-profile | 価値観・ビジョン取得 | `src/api/resume.py` |
| POST | /resume/jobs | 履歴書×求人マッチング分析 | `src/api/resume.py` |
| GET  | /resume/jobs | 分析一覧取得 | `src/api/resume.py` |
| GET  | /resume/jobs/{job_id} | 分析詳細取得 | `src/api/resume.py` |
| POST | /resume/jobs/{job_id}/chat | 面接コーチング（Q&A） | `src/api/resume.py` |
| POST | /resume/jobs/{job_id}/company-questions | 逆質問生成 | `src/api/resume.py` |
| POST | /resume/company-profiles | 企業情報登録 | `src/api/resume.py` |
| GET  | /resume/company-profiles/{company_id} | 企業情報取得 | `src/api/resume.py` |
| PATCH | /resume/company-profiles/{company_id} | 企業情報更新 | `src/api/resume.py` |
| DELETE | /resume/company-profiles/{company_id} | 企業情報削除 | `src/api/resume.py` |
| POST | /knowledge/documents | RAGドキュメント登録 | `src/api/knowledge.py` |
| GET  | /knowledge/documents | ドキュメント一覧取得 | `src/api/knowledge.py` |
| GET  | /knowledge/documents/{doc_id} | ドキュメント詳細取得 | `src/api/knowledge.py` |
| DELETE | /knowledge/documents/{doc_id} | ドキュメント削除 | `src/api/knowledge.py` |
| POST | /search/query | セマンティック検索＋RAG回答 | `src/api/search.py` |
| POST | /search/feedback/{log_id} | 検索フィードバック登録 | `src/api/search.py` |
| GET  | /health | ヘルスチェック | `src/api/main.py` |
