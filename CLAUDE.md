# CLAUDE.md - Project Intelligence

## 🚀 Project Overview

- **Name**: uv-test-20260226
- **Stack**: Python 3.14+, uv, FastAPI, Google Cloud Vertex AI (Gemini 2.5 Flash)
- **Core Goal**: Google Cloud Vertex AIを活用した、構造化データ（JSON）によるマルチモーダル（画像・動画・音声・PDF・テキスト）メディアの高度な解析基盤。

## 🛠 Development Commands

- **Environment Setup**: `uv sync` (依存関係の同期), `uv python install` (ランタイムのインストール)
- **App Execution (Main)**: `uv run main.py`
- **API Execution (FastAPI)**: `uv run uvicorn src.api.main:app --reload`
- **Testing**: `uv run pytest`
- **Linting & Formatting**: `uv run ruff check . --fix`
- **Type Checking**: `uv run mypy .`

## 📏 Coding Standards (2026 Edition)

※詳細は SKILL.md の実装パターンを参照してください。

- **Type System**: Python 3.10+ の `|` (Pipe syntax) を使用し、`str | None` のように記述します（`Optional` は非推奨）。
- **Async Pattern**: Gemini API呼び出しには `client.aio` (Async API) を使用し、一貫して非同期処理を徹底します。
- **Schema Validation**: AIのレスポンス定義には必ず Pydantic `BaseModel` を使用します。
- **Naming**: 変数・関数名は `snake_case`、クラス名は `PascalCase`、定数は `UPPER_SNAKE_CASE` を遵守します。

## 📂 Project Structure

- `src/api/`: FastAPIのエンドポイント定義。
- `src/core/`: Geminiクライアント、ストレージ操作、データスキーマ等の基幹ロジック。
- `tests/`: `pytest-mock` を使用した単体テストおよび結合テスト。
- `upload/`: 処理対象メディアの一時保存用ディレクトリ（`.gitignore` 対象）。

## ⚠️ Important Environment Variables

- `GOOGLE_CLOUD_PROJECT`: Google CloudのプロジェクトID（必須）。
- `GOOGLE_CLOUD_LOCATION`: Vertex AIのリージョン（デフォルト: `asia-northeast1`）。
- `GCS_BUCKET_NAME`: 画像アップロード用のGCSバケット名。
