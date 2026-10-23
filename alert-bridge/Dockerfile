FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.30 /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY bridge ./bridge
RUN useradd --system --uid 10001 app && mkdir -p /data/incidents && chown app /data/incidents
USER app
EXPOSE 8000
CMD ["uvicorn", "bridge.main:app", "--host", "0.0.0.0", "--port", "8000"]
