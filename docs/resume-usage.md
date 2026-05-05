# 職務経歴書 × 求人 AIマッチング 使用ガイド

職務経歴書PDFと企業の求人情報を組み合わせて、
マルチステップAIエージェントが面接対策を自動生成する機能の使い方です。

## 機能概要

```
あなたの職務経歴書PDF  +  企業の求人情報
          ↓
  Geminiを4回呼び出すパイプライン
          ↓
  ① 求人情報の構造化抽出
  ② 職務経歴とのマッチング分析（スキル・経験ベース）
  ③ 想定面接質問 + STAR形式回答例
  ④ ギャップ分析 + 総合適合スコア
          ↓
  Firestoreに保存（後から何度でも参照可）
```

---

## 事前準備

サーバーを起動してから操作してください。

```bash
uv run uvicorn src.api.main:app --reload
```

Web UIは `http://localhost:8000/resume` で利用できます。
APIドキュメント（Swagger UI）は `http://localhost:8000/docs` で確認できます。

---

## Step 1: 職務経歴書の登録

職務経歴書PDFをアップロードすると、Geminiが自動でスキル・職歴・サマリーを抽出してFirestoreに保存します。
**一度登録すれば、以降の求人分析で自動的に参照されます。**

### Web UIで操作する場合（推奨）

1. `http://localhost:8000/resume` を開く
2. APIキーを入力して「保存」
3. 「職務経歴書PDFをアップロード」でPDFを選択
4. 「アップロード」ボタンをクリック
5. 登録が完了すると直近の職歴とスキル一覧が表示される

### curlで操作する場合

```bash
curl -X POST "http://localhost:8000/resume/profile" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "file=@/path/to/resume.pdf"
```

### レスポンス例

```json
{
  "skills": ["Python", "FastAPI", "SQL", "プロジェクトマネジメント"],
  "work_experiences": [
    {
      "company": "○○株式会社",
      "role": "バックエンドエンジニア",
      "period": "2022年4月 〜 現在",
      "description": "FastAPIを用いたAPIサーバーの設計・開発",
      "achievements": ["月間100万リクエストを処理するAPIを構築", "レビュープロセス導入でバグ件数を30%削減"]
    }
  ],
  "summary": "バックエンド開発を中心に5年の経験を持つエンジニア...",
  "raw_text": "（PDFの全文テキスト）",
  "source_gcs_uri": "gs://バケット名/resume.pdf"
}
```

### 登録済みプロフィールの確認

```bash
curl "http://localhost:8000/resume/profile" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

---

## Step 2: 求人分析の実行

求人情報を投げると、AIエージェントが4段階の分析を順番に実行します。
**Geminiを4回呼び出すため、完了まで30〜60秒かかります。**

### Web UIで操作する場合（推奨）

1. 「テキスト入力」または「URL入力」を選択
2. 求人テキストを貼り付けるか、求人ページのURLを入力
3. 「分析を実行」ボタンをクリック
4. 完了後、以下のタブで結果を確認できる
   - **経歴マッチング**: 職務経歴の何がどう活かせるか（優先度順）
   - **面接Q&A**: 想定質問とSTAR形式の回答例（クリックで展開）
   - **ギャップ分析**: 不足スキルの対策・アピール方法

### curlで操作する場合（テキスト）

```bash
# 求人テキストをファイルに保存してから送る
cat > /tmp/job.txt << 'EOF'
企業名: ○○株式会社
職種: バックエンドエンジニア
必須スキル: Python, FastAPI, SQL
求める人物像: 自律的に動ける方
（求人ページからコピーしたテキストをそのまま貼り付ける）
EOF

curl -X POST "http://localhost:8000/resume/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "text=</tmp/job.txt"
```

### curlで操作する場合（URL）

```bash
curl -X POST "http://localhost:8000/resume/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "url=https://example.com/jobs/12345"
```

> [!IMPORTANT]
> ログインが必要なページ、JavaScriptで動的に描画されるページはURLからの取得に失敗します。
> その場合はテキストをコピーして `text` フィールドで送ってください。

### レスポンス例

```json
{
  "job_id": "a3f9b2c1...",
  "job_posting_company": "○○株式会社",
  "job_posting_role": "バックエンドエンジニア",
  "job_posting_required_skills": ["Python", "FastAPI", "SQL"],
  "job_posting_desired_person": "自律的に動ける方",
  "job_posting_culture": "フラットな組織文化",
  "experience_matches": [
    {
      "skill_or_experience": "FastAPI開発経験",
      "relevance_reason": "直近のプロジェクトでFastAPIを用いたAPI設計を担当しており...",
      "priority": 1
    }
  ],
  "interview_questions": [
    {
      "question": "技術的に困難な問題をどう解決しましたか？",
      "answer_example": "（STAR形式の回答例）",
      "experience_used": ["FastAPI開発経験", "SQLチューニング"]
    }
  ],
  "gap_analysis": "必須スキルのうちSQLは実務経験があるが...",
  "overall_fit_score": 0.78,
  "created_at": "2026-05-05T12:00:00+00:00"
}
```

---

## 分析結果の参照

Firestoreに保存された分析結果は後から何度でも参照できます。
Web UIの「過去の分析」一覧からクリックするだけで再表示できます。

### 全求人の一覧取得（作成日時の降順）

```bash
curl "http://localhost:8000/resume/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

### 特定の分析結果を取得

```bash
curl "http://localhost:8000/resume/jobs/{job_id}" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

---

## Firestoreでのデータ確認

[Google Cloud Console](https://console.cloud.google.com/firestore/databases) → Firestore Database → データ

```
(default) データベース
├── resume_profiles/
│   └── current           ← 職務経歴書プロフィール（1ドキュメント固定）
└── resume_job_analyses/
    ├── a3f9b2c1...       ← 求人分析結果（企業ごと）
    └── d7e4f0a2...
```

---

## StrengthsFinderエージェントとの違い

| | StrengthsFinderエージェント (`/agent`) | 職務経歴書マッチング (`/resume`) |
|---|---|---|
| 入力 | CliftonStrengths結果PDF | 職務経歴書PDF |
| マッチング軸 | 資質・強み（34の資質） | スキル・経験・実績 |
| 向いている場面 | 強みを活かした自己PR | 具体的な経験・スキルのアピール |
