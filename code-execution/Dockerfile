FROM python:3.14.4-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir . \
    && useradd --uid 10001 --no-create-home executor

USER executor
ENV WORK_ROOT=/work
EXPOSE 8001
# One worker: the job semaphore is per process. Scale with more containers instead.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
