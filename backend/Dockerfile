FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.30 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /app

# Dependencies first for layer caching.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY README.md alembic.ini ./
COPY migrations ./migrations
COPY src ./src
RUN uv sync --frozen --no-dev

ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA

RUN useradd --system --uid 10001 app
USER app
EXPOSE 8000

# api (default): migrate, then serve. The worker overrides the command.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn matchday.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
