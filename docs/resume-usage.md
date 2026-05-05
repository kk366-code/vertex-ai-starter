# 職務経歴書 × 求人 AIマッチング 使用ガイド

職務経歴書PDFと企業の求人情報を組み合わせて、
マルチステップAIエージェントが面接対策を自動生成する機能の使い方です。

## 機能概要

```
あなたの職務経歴書PDF  +  企業の求人情報  [+  企業プロフィール（任意）]
          ↓
  Geminiを4〜N回呼び出すパイプライン
          ↓
  ① 求人情報の構造化抽出
  ② 職務経歴とのマッチング分析（スキル・経験・価値観ベース）
  ③ 想定面接質問 + STAR形式回答例（あなたらしさを反映）
  ④ ギャップ分析 + 総合適合スコア
          ↓
  Firestoreに保存（後から何度でも参照可）
```

### 企業プロフィール機能（追加機能）

求人票1枚だけでなく、複数ソースから企業情報を集めてAIが統合します。
一度作成した企業プロフィールは複数の求人分析で使い回せます。

```
採用ページURL + 技術ブログURL（複数）+ 社員インタビューURL + フリーテキスト + PDF資料
          ↓
  Geminiが全ソースを統合 → 企業プロフィール（Firestoreに保存）
          ↓
  求人分析パイプラインに自動注入
  → マッチング・Q&A・ギャップ分析が企業文化・技術スタックを考慮した精度に向上
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


## Step 1.1: パーソナルプロフィールの登録（任意・推奨）

職務経歴書だけでは伝わらない「あなたらしさ」を事前登録しておくと、面接Q&Aの回答例がより具体的・個性的になります。
**一度登録すれば以降の全ての求人分析で自動的に参照されます。**

### 登録できる情報

| フィールド | 説明 | 例 |
|---|---|---|
| `values` | 価値観・信条 | `["自律と信頼", "学び続けること"]` |
| `influential_items` | 影響を受けた本・人 | `["ティール組織", "〇〇さん（元上司）"]` |
| `episodes` | 印象的なエピソード（STAR形式） | 下記参照 |
| `career_vision` | キャリアビジョン（5〜10年後） | `"プロダクト全体を技術で支えるCTOになりたい"` |
| `work_style` | 働き方の好み | `"裁量を持って自律的に動けるチームが理想"` |

### Web UIで操作する場合（推奨）

1. 「★ パーソナルプロフィール」セクションの「▼ 編集する」をクリック
2. 各フィールドを入力（価値観・影響を受けた本/人は改行区切りで複数入力可）
3. STARエピソードは「+ 追加」ボタンで追加し、S/T/A/R を入力
4. 「保存する」をクリック

### curlで操作する場合

### 登録済みプロフィールの確認

```bash
curl "http://localhost:8000/resume/personal-profile" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

パーソナルプロフィールを登録すると、面接Q&Aの回答例に「なぜそれをやったか」「どんな人間か」が自然に反映されます。未登録でも問題なく動作します。

> [!NOTE]
> パーソナルプロフィールは上書き保存方式です。再度 POST すると内容が更新されます。


## Step 1.2: 企業プロフィールの作成（任意・推奨）

求人票だけでは得られない企業情報を複数ソースから収集し、AIが統合したプロフィールを作成します。
**一度作成すれば、同じ企業への複数の求人分析で使い回せます。**

### Web UIで操作する場合（推奨）

1. 「企業プロフィール」セクションの「新しい企業プロフィールを作成」をクリック
2. 以下の情報を入力（最低1つ必須）:
   - **採用ページ URL**: 企業の採用トップページなど
   - **技術ブログ URL**: エンジニアブログの記事URLを1行1つで複数入力
   - **社員インタビュー URL**: Wantedly・1on1記事など
   - **フリーテキスト**: 会社説明会のメモ、LinkedInの概要など
   - **企業説明 PDF**: 会社説明スライド（複数可）
3. 「企業プロフィールを作成する」をクリック（30〜60秒かかります）
4. 作成されたプロフィールが一覧に表示されたら「使用する」をクリック
5. Step 2の求人分析で自動的に企業プロフィールが注入される

> [!IMPORTANT]
> ログインが必要なページ、JavaScriptで動的に描画されるページはURLからの取得に失敗します。
> その場合はテキストをコピーして「フリーテキスト」に貼り付けてください。

### curlで操作する場合

```bash
# テキストのみで企業プロフィールを作成
curl -X POST "http://localhost:8000/resume/company-profiles" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "company_name=○○株式会社" \
  -F "free_text=〇〇株式会社はBtoBのSaaS企業で、エンジニアは自律的に動くことが求められる..."

# URLを指定して企業プロフィールを作成
curl -X POST "http://localhost:8000/resume/company-profiles" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "hiring_page_url=https://company.com/careers" \
  -F "tech_blog_urls_text=https://tech.company.com/entry/1
https://tech.company.com/entry/2" \
  -F "employee_interview_urls_text=https://wantedly.com/..."

# PDFも組み合わせる
curl -X POST "http://localhost:8000/resume/company-profiles" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "company_name=○○株式会社" \
  -F "pdf_files=@/path/to/company_deck.pdf" \
  -F "free_text=補足メモ..."
```

### 企業プロフィール一覧の取得

```bash
curl "http://localhost:8000/resume/company-profiles" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```

### 特定の企業プロフィールの取得

```bash
curl "http://localhost:8000/resume/company-profiles/{company_id}" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}"
```
curl -X POST "http://localhost:8000/resume/personal-profile" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "values": ["自律と信頼", "学び続けること"],
    "influential_items": ["ティール組織（組織観が変わった）", "〇〇さん（元上司）"],
    "career_vision": "プロダクト全体を技術で支えるCTOになりたい",
    "work_style": "裁量を持って自律的に動けるチームが理想",
    "episodes": [
      {
        "title": "チームを立て直した経験",
        "situation": "リリース直前に主要メンバーが離脱し、3人で対応することになった",
        "task": "残ったメンバーで工数を再配分し、スコープを絞りながらリリースを守る",
        "action": "毎朝15分の同期MTGを設け、優先度をその場で決め直すフローを導入した",
        "result": "予定通りリリースでき、その後もそのフローが組織の標準になった"
      }
    ]
  }'
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
curl -X POST "http://localhost:8000/resume/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "text=企業名: ○○株式会社 職種: バックエンドエンジニア 必須スキル: Python, FastAPI..."
```

### curlで操作する場合（URL）

```bash
curl -X POST "http://localhost:8000/resume/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "url=https://example.com/jobs/12345"
```

### 企業プロフィールを使って分析する場合

```bash
# 先に企業プロフィールを作成してcompany_idを取得しておく
curl -X POST "http://localhost:8000/resume/jobs" \
  -H "X-API-KEY: ${INTERNAL_API_KEY}" \
  -F "text=（求人テキスト）" \
  -F "company_profile_id=a3f9b2c1..."
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
│   └── current                  ← 職務経歴書プロフィール（1ドキュメント固定）
├── personal_profiles/
│   └── current                  ← パーソナルプロフィール（1ドキュメント固定）
├── company_profiles/
│   ├── a3f9b2c1...              ← 企業プロフィール（企業ごと）
│   └── d7e4f0a2...
└── resume_job_analyses/
    ├── c1e5f9b3...              ← 求人分析結果（求人ごと）
    └── f2a7d4c8...
```

---

## StrengthsFinderエージェントとの違い

| | StrengthsFinderエージェント (`/agent`) | 職務経歴書マッチング (`/resume`) |
|---|---|---|
| 入力 | CliftonStrengths結果PDF | 職務経歴書PDF |
| マッチング軸 | 資質・強み（34の資質） | スキル・経験・実績 |
| 向いている場面 | 強みを活かした自己PR | 具体的な経験・スキルのアピール |
