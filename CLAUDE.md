# CLAUDE.md - Project Intelligence

## 🚀 Project Overview

- **Name**: uv-test-20260226
- **Stack**: Python 3.14+, uv, FastAPI, Google Cloud Vertex AI (Gemini 2.5 Flash)
- **Core Goal**: Vertex AIを活用したマルチモーダルメディア解析基盤。

## 📚 詳細ドキュメント

| ファイル | 内容 | 参照タイミング |
|---------|------|--------------|
| **SKILL.md** | 実装パターン・Gemini呼び出し・Known Pitfalls | API追加・修正時 |
| **FRONTEND.md** | テンプレート・htmx・Tailwind規約 | UI追加時 |
| **API_MAP.md** | 実装済みエンドポイント一覧 | 新API追加前 |

## 🛠 Development Commands

- **Environment Setup**: `uv sync` (依存関係の同期), `uv python install` (ランタイムのインストール)
- **API Execution (FastAPI)**: `uv run uvicorn src.api.main:app --reload`
- **Testing**: `uv run pytest`
- **Linting & Formatting**: `uv run ruff format . && uv run ruff check . --fix`
- **Type Checking**: `uv run mypy .`

## 📏 Coding Standards

- **Types**: `str | None` 形式（`Optional` 禁止）
- **Async**: Gemini呼び出しは `client.aio` で非同期統一
- **Schema**: AIレスポンスには必ず Pydantic `BaseModel`
- **Naming**: `snake_case` / `PascalCase` / `UPPER_SNAKE_CASE`
- 詳細・Known Pitfalls は **SKILL.md** を参照

## 📂 Project Structure

- `src/api/` — FastAPIルーター（新規追加パターンは **SKILL.md** 参照）
- `src/core/` — Geminiクライアント・スキーマ・ストレージ等
- `src/api/templates/` — Jinja2テンプレート（UI規約は **FRONTEND.md** 参照）
- `tests/` — pytest-mock を使った単体・結合テスト

## 📝 Git & PR Convention

- **タイトル（1行目）**: 英語で記述する。例: `feat: add agent UI`, `fix: handle empty URL response`
- **本文（3行目以降）**: 日本語で記述する。何を・なぜ変えたかを説明する。
- **PRの作成**: 実装完了後は必ずプルリクエストを作成する。既存のPRがマージ済みの場合は、新しいPRを作成する（マージ済みPRには追加しない）。PR作成前に `git fetch origin main` で最新の main を取得し、`git log origin/main..HEAD` でそのPRに含まれるコミットを確認すること。
- **PR作成後のセッション引き継ぎ**: PRを作成したら、次のセッションへの引き継ぎテキストを必ず出力する。以下の形式で記述すること：

  ```
  ## 次のセッションへの引き継ぎ

  ### 作成したPR
  - PR URL: <URL>
  - 概要: <何を実装したか1〜2文>

  ### 現在のブランチ状態
  - ブランチ名: <branch>
  - 対象ファイル: <主な変更ファイル>

  ### 次にやること（あれば）
  - <残タスクや懸念点>
  ```

## ⚠️ Important Environment Variables

- `GOOGLE_CLOUD_PROJECT`: Google CloudのプロジェクトID（必須）。
- `GOOGLE_CLOUD_LOCATION`: Vertex AIのリージョン（デフォルト: `asia-northeast1`）。
- `GCS_BUCKET_NAME`: 画像アップロード用のGCSバケット名。
