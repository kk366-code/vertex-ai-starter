# AIエージェント機能 使用ガイド

CliftonStrengths（ストレングスファインダー）の結果PDFと企業の求人情報を組み合わせて、
マルチステップAIエージェントが面接対策を自動生成する機能の使い方です。

## 機能概要

```
あなたのStrengths PDF  +  企業の求人情報
          ↓
  Geminiを4回呼び出すパイプライン
          ↓
  ① 求人情報の構造化抽出
  ② 強みとのマッチング分析
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

APIドキュメント（Swagger UI）は `http://localhost:8000/docs` で確認できます。

---

## Step 1: StrengthsProfile の登録

CliftonStrengths の結果PDFをアップロードすると、Geminiが自動でTop5を抽出してFirestoreに保存します。
**一度登録すれば、以降の求人分析で自動的に参照されます。**

### Swagger UIで操作する場合

1. `http://localhost:8000/docs` を開く
2. `POST /strengths/profile` → **Try it out**
3. `file` にPDFファイルを選択
4. `X-API-KEY` ヘッダーに `.env` の `INTERNAL_API_KEY` を入力
5. **Execute**

### curlで操作する場合

```bash
curl -X POST "http://localhost:8000/strengths/profile" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "file=@/path/to/strengths.pdf"
```

### レスポンス例

```json
{
  "top5": [
    {
      "name": "ポジティブ",
      "english_name": "Positivity",
      "domain": "人間関係構築力",
      "description": "前向きで周囲を明るくする..."
    }
  ],
  "raw_text": "PDFの全文テキスト",
  "source_gcs_uri": "gs://バケット名/strengths.pdf"
}
```

### 登録済みプロフィールの確認

```bash
curl "http://localhost:8000/strengths/profile" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

---

## Step 2: 求人分析の実行

求人情報を投げると、AIエージェントが4段階の分析を順番に実行します。
**Geminiを4回呼び出すため、完了まで30〜60秒かかります。**

### 求人テキストの準備

ログインが必要な求人サイトなど、URLを直接指定できない場合は、
求人ページのテキストをコピーしてファイルに保存してください。

```bash
# 求人テキストをファイルに保存する
cat > /tmp/job.txt << 'EOF'
企業名: ○○株式会社
職種: バックエンドエンジニア
必須スキル: Python, FastAPI, SQL
求める人物像: 自律的に動ける方
（求人ページからコピーしたテキストをそのまま貼り付ける）
EOF
```

### Swagger UIで操作する場合（推奨）

1. `POST /jobs` → **Try it out**
2. `text` フィールドに求人テキストを貼り付け（改行・特殊文字も問題なし）
3. `url` フィールドは空のまま
4. **Execute**

### curlで操作する場合（テキストファイル使用）

```bash
# ファイルの中身をフィールド値として送る（< を使う）
curl -X POST "http://localhost:8000/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "text=</tmp/job.txt"
```

> [!NOTE]
> `-F "text=<ファイルパス"` の `<` はファイルの中身をフィールド値として送る構文です。
> `@` はファイル自体をアップロードするため、ここでは使いません。

### 公開URLを直接指定する場合

```bash
curl -X POST "http://localhost:8000/jobs" \
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
  "job_posting": {
    "company_name": "○○株式会社",
    "role": "バックエンドエンジニア",
    "required_skills": ["Python", "FastAPI", "SQL"],
    "desired_person": "自律的に動ける方",
    "culture": "フラットな組織文化",
    "raw_text": "..."
  },
  "strength_matches": [
    {
      "strength_name": "学習欲",
      "relevance_reason": "新技術への適応が求められる職種に最適...",
      "priority": 1
    }
  ],
  "interview_questions": [
    {
      "question": "技術的に困難な問題をどう解決しましたか？",
      "answer_example": "学習欲を活かして...",
      "strengths_used": ["学習欲"]
    }
  ],
  "gap_analysis": "強みで補完できる部分は...",
  "overall_fit_score": 0.82,
  "created_at": "2026-05-04T12:00:00+00:00"
}
```

---

## 分析結果の参照

Firestoreに保存された分析結果は後から何度でも参照できます。

### 全企業の一覧取得（作成日時の降順）

```bash
curl "http://localhost:8000/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

### 特定企業の分析結果を取得

```bash
curl "http://localhost:8000/jobs/{job_id}" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

`job_id` は `POST /jobs` のレスポンスに含まれる16進数の文字列です。

---

## Firestoreでのデータ確認

[Google Cloud Console](https://console.cloud.google.com/firestore/databases) → Firestore Database → データ

```
(default) データベース
├── strengths_profiles/
│   └── current           ← StrengthsProfile（1ドキュメント固定）
└── job_analyses/
    ├── a3f9b2c1...       ← 求人分析結果（企業ごと）
    └── d7e4f0a2...
```
