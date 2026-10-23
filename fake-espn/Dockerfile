# Build context is the repo root (see compose.yaml) so the recorded fixtures are baked in.
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "fastapi==0.115.*" "uvicorn==0.32.*"
COPY fake-espn/app.py .
COPY backend/tests/fixtures /fixtures
ENV FIXTURES_DIR=/fixtures
RUN useradd --system --uid 10001 app
USER app
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
