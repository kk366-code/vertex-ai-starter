# ステージ1: ビルド環境
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# ファイルをコピーして依存関係をインストール（--mountを使わない）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ステージ2: 実行環境
FROM python:3.14-slim-bookworm
WORKDIR /app

# ビルド済みの仮想環境をコピー
COPY --from=builder /app/.venv /app/.venv
COPY . .

# 仮想環境のパスを通す
ENV PATH="/app/.venv/bin:$PATH"

# ポート8080で起動
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
