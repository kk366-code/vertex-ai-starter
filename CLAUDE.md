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
- **Linting & Formatting**: `uv run ruff format . && uv run ruff check . --fix`
- **Type Checking**: `uv run mypy .`

## 📏 Coding Standards (2026 Edition)

※詳細は SKILL.md の実装パターンを参照してください。

- **Type System**: Python 3.10+ の `|` (Pipe syntax) を使用し、`str | None` のように記述します（`Optional` は非推奨）。
- **Async Pattern**: Gemini API呼び出しには `client.aio` (Async API) を使用し、一貫して非同期処理を徹底します。
- **Schema Validation**: AIのレスポンス定義には必ず Pydantic `BaseModel` を使用します。
- **Naming**: 変数・関数名は `snake_case`、クラス名は `PascalCase`、定数は `UPPER_SNAKE_CASE` を遵守します。
- **External API Response Nullability**: Google SDK（google-genai, google-cloud-firestore等）のレスポンスフィールドは `| None` を含む型定義が多い。フィールドへのアクセス前に必ず None チェックを行い、mypy エラーを防ぐこと（詳細は SKILL.md の「Known Pitfalls」を参照）。

## 📂 Project Structure

- `src/api/`: FastAPIのエンドポイント定義。
- `src/core/`: Geminiクライアント、ストレージ操作、データスキーマ等の基幹ロジック。
- `tests/`: `pytest-mock` を使用した単体テストおよび結合テスト。
- `upload/`: 処理対象メディアの一時保存用ディレクトリ（`.gitignore` 対象）。

## 📜 FastAPI Implementation Conventions

- **Dependency Injection**: `Form`, `File`, `Security`, `Depends` を使用する際は、必ず `typing.Annotated` を使用する（Ruff B008 回避と型安全のため）。
- **File Upload & Temporary Storage**:
  - クライアントからのファイルは一度 `upload/` 内の「一時フォルダ」に保存する。
  - `tempfile.TemporaryDirectory(dir=Path("upload"))` を使用し、作業完了後（またはエラー時）に自動削除されるように設計する。
  - 元ファイルを破壊・削除しないよう、パスの分離を徹底する。

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
