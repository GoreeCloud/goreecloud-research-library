FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GORECLOUD_RESEARCH_DATA_DIR=/data

WORKDIR /app

RUN addgroup --system goreecloud && adduser --system --ingroup goreecloud goreecloud

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .

RUN mkdir -p /data && chown -R goreecloud:goreecloud /data /app
USER goreecloud

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
