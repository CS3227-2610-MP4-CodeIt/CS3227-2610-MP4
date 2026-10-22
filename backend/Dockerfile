# Build from the repo root so the schema in specs/ can be copied:
#   docker build -f backend/Dockerfile -t backend .
FROM python:3.14.4-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY specs/backend-schema.sql ./backend-schema.sql
RUN pip install --no-cache-dir . \
    && useradd --uid 10002 --no-create-home appuser \
    && mkdir -p /data && chown appuser /data

USER appuser
ENV DATABASE_PATH=/data/app.db
VOLUME /data
EXPOSE 8000
# One worker: background jobs and the SSE hub live in this process (spec §2).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
