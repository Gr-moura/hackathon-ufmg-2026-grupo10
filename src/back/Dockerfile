FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# System deps + Python 3.12 (nativo no Ubuntu 24.04)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    gcc \
    libpq-dev \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-por \
    ca-certificates \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

# Node 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Cria virtualenv e atualiza pip dentro dele
RUN python3.12 -m venv $VIRTUAL_ENV \
    && pip install --upgrade pip==25.1.1 setuptools==81.0.0

# Pinned Python dependencies (from pip freeze on dev machine)
RUN pip install --no-cache-dir \
    alembic==1.18.4 \
    annotated-types==0.7.0 \
    anyio==4.13.0 \
    bcrypt==5.0.0 \
    beautifulsoup4==4.14.3 \
    certifi==2026.2.25 \
    cffi==2.0.0 \
    charset-normalizer==3.4.7 \
    click==8.3.2 \
    cryptography==46.0.7 \
    distro==1.9.0 \
    ecdsa==0.19.2 \
    et_xmlfile==2.0.0 \
    fastapi==0.136.0 \
    filelock==3.28.0 \
    fsspec==2026.3.0 \
    greenlet==3.4.0 \
    h11==0.16.0 \
    httpcore==1.0.9 \
    httptools==0.7.1 \
    httpx==0.28.1 \
    idna==3.11 \
    Jinja2==3.1.6 \
    jiter==0.14.0 \
    joblib==1.5.3 \
    lxml==6.0.4 \
    Mako==1.3.11 \
    MarkupSafe==3.0.3 \
    mpmath==1.3.0 \
    networkx==3.6.1 \
    numpy==2.4.4 \
    openai==2.32.0 \
    openpyxl==3.1.5 \
    pandas==3.0.2 \
    passlib==1.7.4 \
    "pdfminer.six==20251230" \
    pdfplumber==0.11.9 \
    pgvector==0.4.2 \
    pillow==12.2.0 \
    playwright==1.58.0 \
    psycopg==3.3.3 \
    psycopg-binary==3.3.3 \
    pyasn1==0.6.3 \
    pycparser==3.0 \
    pydantic==2.13.2 \
    pydantic-settings==2.13.1 \
    pydantic_core==2.46.2 \
    pyee==13.0.1 \
    pypdfium2==5.7.0 \
    python-dateutil==2.9.0.post0 \
    python-dotenv==1.2.2 \
    python-jose==3.5.0 \
    python-multipart==0.0.26 \
    PyYAML==6.0.3 \
    regex==2026.4.4 \
    requests==2.33.1 \
    rsa==4.9.1 \
    scikit-learn==1.8.0 \
    scipy==1.17.1 \
    six==1.17.0 \
    sniffio==1.3.1 \
    soupsieve==2.8.3 \
    SQLAlchemy==2.0.49 \
    starlette==1.0.0 \
    sympy==1.14.0 \
    threadpoolctl==3.6.0 \
    tiktoken==0.12.0 \
    tqdm==4.67.3 \
    typing-inspection==0.4.2 \
    typing_extensions==4.15.0 \
    urllib3==2.6.3 \
    uvicorn==0.44.0 \
    uvloop==0.22.1 \
    watchfiles==1.1.1 \
    websockets==16.0 \
    xgboost==3.2.0

# Install Playwright browsers
RUN playwright install --with-deps chromium

WORKDIR /app

RUN pip install --no-cache-dir \
    torch>=2.1.0 \
    scikit-learn>=1.3.0 \
    numpy>=1.24.0 \
    --extra-index-url https://download.pytorch.org/whl/cpu
COPY pyproject.toml .
RUN mkdir -p app && touch app/__init__.py && \
    pip install --no-cache-dir .[dev]

COPY . .

RUN pip install --no-cache-dir .[dev] && \
    chmod +x scripts/init_db.sh

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "scripts/init_db.sh"]
