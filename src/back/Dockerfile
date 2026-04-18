FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    libpq-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --upgrade pip setuptools && \
    pip install --no-cache-dir .[dev]

COPY . .

RUN chmod +x scripts/init_db.sh

EXPOSE 8000
ENTRYPOINT ["scripts/init_db.sh"]
