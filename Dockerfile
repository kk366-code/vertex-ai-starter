# ステージ1: ビルド環境
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# ステージ2: 実行環境
FROM python:3.14-slim-bookworm
WORKDIR /app
# ビルド済みの仮想環境をコピー
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"

# Cloud Run は 8080 ポートを期待する
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
