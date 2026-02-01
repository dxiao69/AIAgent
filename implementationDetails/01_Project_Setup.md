# 01 - Project Setup Guide

## Overview

This guide walks you through setting up the complete project structure, development environment, and Docker configuration for the IT Operations AI Agent.

---

## Prerequisites

- Python 3.11+ installed
- Docker Desktop installed and running
- Git installed
- VS Code (recommended) with Python extension

---

## Step 1: Create Project Structure

### 1.1 Create the Root Directory

```powershell
mkdir itoa-agent
cd itoa-agent
git init
```

### 1.2 Create Full Project Structure

📝 **PROMPT: Create project folder structure**
```
Create a Python monorepo project structure for an IT Operations AI Agent with:
- 4 microservices: auth-service, core-service, llm-service, action-worker
- 1 desktop application using PySide6
- 1 shared library package
- Kubernetes deployment configs
- Docker Compose for local development
- Requirements files for base, dev, and test dependencies

Show me the commands to create all folders and empty __init__.py files.
```

**Execute these commands:**

```powershell
# Root files
New-Item -ItemType File -Path "README.md"
New-Item -ItemType File -Path "docker-compose.yml"
New-Item -ItemType File -Path "docker-compose.dev.yml"
New-Item -ItemType File -Path ".gitlab-ci.yml"
New-Item -ItemType File -Path "pyproject.toml"
New-Item -ItemType File -Path ".gitignore"
New-Item -ItemType File -Path ".env.example"

# Requirements
New-Item -ItemType Directory -Path "requirements" -Force
New-Item -ItemType File -Path "requirements/base.txt"
New-Item -ItemType File -Path "requirements/dev.txt"
New-Item -ItemType File -Path "requirements/test.txt"

# Services - Auth
New-Item -ItemType Directory -Path "services/auth-service/src/auth_service" -Force
New-Item -ItemType File -Path "services/auth-service/Dockerfile"
New-Item -ItemType File -Path "services/auth-service/pyproject.toml"
New-Item -ItemType File -Path "services/auth-service/src/auth_service/__init__.py"
New-Item -ItemType File -Path "services/auth-service/src/auth_service/main.py"
New-Item -ItemType File -Path "services/auth-service/src/auth_service/config.py"
New-Item -ItemType File -Path "services/auth-service/src/auth_service/routes.py"
New-Item -ItemType File -Path "services/auth-service/src/auth_service/models.py"
New-Item -ItemType File -Path "services/auth-service/src/auth_service/oauth.py"
New-Item -ItemType File -Path "services/auth-service/src/auth_service/jwt_handler.py"

# Services - Core
New-Item -ItemType Directory -Path "services/core-service/src/core_service" -Force
New-Item -ItemType File -Path "services/core-service/Dockerfile"
New-Item -ItemType File -Path "services/core-service/pyproject.toml"
New-Item -ItemType File -Path "services/core-service/src/core_service/__init__.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/main.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/config.py"

# Core service submodules
New-Item -ItemType Directory -Path "services/core-service/src/core_service/api" -Force
New-Item -ItemType File -Path "services/core-service/src/core_service/api/__init__.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/api/rules.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/api/scans.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/api/devices.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/api/applications.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/api/actions.py"

New-Item -ItemType Directory -Path "services/core-service/src/core_service/models" -Force
New-Item -ItemType File -Path "services/core-service/src/core_service/models/__init__.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/models/rule.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/models/device.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/models/application.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/models/scan.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/models/action.py"

New-Item -ItemType Directory -Path "services/core-service/src/core_service/services" -Force
New-Item -ItemType File -Path "services/core-service/src/core_service/services/__init__.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/services/rule_engine.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/services/scan_engine.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/services/query_builder.py"

New-Item -ItemType Directory -Path "services/core-service/src/core_service/connectors" -Force
New-Item -ItemType File -Path "services/core-service/src/core_service/connectors/__init__.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/connectors/mecm.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/connectors/servicenow.py"
New-Item -ItemType File -Path "services/core-service/src/core_service/connectors/tachyon.py"

# Services - LLM
New-Item -ItemType Directory -Path "services/llm-service/src/llm_service" -Force
New-Item -ItemType File -Path "services/llm-service/Dockerfile"
New-Item -ItemType File -Path "services/llm-service/pyproject.toml"
New-Item -ItemType File -Path "services/llm-service/src/llm_service/__init__.py"
New-Item -ItemType File -Path "services/llm-service/src/llm_service/main.py"
New-Item -ItemType File -Path "services/llm-service/src/llm_service/config.py"
New-Item -ItemType File -Path "services/llm-service/src/llm_service/providers.py"
New-Item -ItemType File -Path "services/llm-service/src/llm_service/prompts.py"
New-Item -ItemType File -Path "services/llm-service/src/llm_service/data_filter.py"
New-Item -ItemType File -Path "services/llm-service/src/llm_service/routes.py"

# Services - Action Worker
New-Item -ItemType Directory -Path "services/action-worker/src/action_worker" -Force
New-Item -ItemType File -Path "services/action-worker/Dockerfile"
New-Item -ItemType File -Path "services/action-worker/pyproject.toml"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/__init__.py"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/celery_app.py"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/config.py"

New-Item -ItemType Directory -Path "services/action-worker/src/action_worker/tasks" -Force
New-Item -ItemType File -Path "services/action-worker/src/action_worker/tasks/__init__.py"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/tasks/base.py"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/tasks/mecm_tasks.py"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/tasks/servicenow_tasks.py"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/tasks/tachyon_tasks.py"
New-Item -ItemType File -Path "services/action-worker/src/action_worker/tasks/notification_tasks.py"

# Desktop
New-Item -ItemType Directory -Path "desktop/src/itoa_desktop" -Force
New-Item -ItemType File -Path "desktop/pyproject.toml"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/__init__.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/main.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/app.py"

New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/config" -Force
New-Item -ItemType File -Path "desktop/src/itoa_desktop/config/__init__.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/config/settings.py"

New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/services" -Force
New-Item -ItemType File -Path "desktop/src/itoa_desktop/services/__init__.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/services/api_client.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/services/auth_service.py"

New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/viewmodels" -Force
New-Item -ItemType File -Path "desktop/src/itoa_desktop/viewmodels/__init__.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/viewmodels/base.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/viewmodels/dashboard_vm.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/viewmodels/rules_vm.py"

New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/views" -Force
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/__init__.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/main_window.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/login_dialog.py"

New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/views/dashboard" -Force
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/dashboard/__init__.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/dashboard/dashboard_view.py"

New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/views/rules" -Force
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/rules/__init__.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/rules/rules_list.py"
New-Item -ItemType File -Path "desktop/src/itoa_desktop/views/rules/rule_builder.py"

New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/resources/styles" -Force
New-Item -ItemType Directory -Path "desktop/src/itoa_desktop/resources/icons" -Force

# Shared
New-Item -ItemType Directory -Path "shared/src/itoa_shared" -Force
New-Item -ItemType File -Path "shared/pyproject.toml"
New-Item -ItemType File -Path "shared/src/itoa_shared/__init__.py"
New-Item -ItemType File -Path "shared/src/itoa_shared/models.py"
New-Item -ItemType File -Path "shared/src/itoa_shared/constants.py"
New-Item -ItemType File -Path "shared/src/itoa_shared/utils.py"
New-Item -ItemType File -Path "shared/src/itoa_shared/exceptions.py"

# Kubernetes
New-Item -ItemType Directory -Path "k8s/base" -Force
New-Item -ItemType Directory -Path "k8s/staging" -Force
New-Item -ItemType Directory -Path "k8s/production" -Force
New-Item -ItemType File -Path "k8s/base/namespace.yaml"
New-Item -ItemType File -Path "k8s/base/configmap.yaml"
New-Item -ItemType File -Path "k8s/base/secrets.yaml"

# Scripts
New-Item -ItemType Directory -Path "scripts" -Force
New-Item -ItemType File -Path "scripts/setup-dev.ps1"
New-Item -ItemType File -Path "scripts/run-tests.ps1"

# Tests
New-Item -ItemType Directory -Path "tests/unit" -Force
New-Item -ItemType Directory -Path "tests/integration" -Force
New-Item -ItemType Directory -Path "tests/ground_truth" -Force
New-Item -ItemType File -Path "tests/__init__.py"
New-Item -ItemType File -Path "tests/conftest.py"

# Docs
New-Item -ItemType Directory -Path "docs" -Force
```

---

## Step 2: Configure Root Files

### 2.1 Create .gitignore

📝 **PROMPT: Generate Python .gitignore**
```
Generate a comprehensive .gitignore for a Python monorepo project with:
- FastAPI microservices
- PySide6 desktop app
- Docker
- VS Code
- pytest
- mypy
- Virtual environments
```

**File: `.gitignore`**

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
pytest_results/

# Translations
*.mo
*.pot

# Environments
.env
.env.local
.env.*.local
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.python-version

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# Logs
logs/
*.log

# Local development
local/
tmp/
temp/

# Database
*.db
*.sqlite

# Secrets (never commit these!)
secrets/
*.pem
*.key

# Desktop app builds
desktop/build/
desktop/dist/
*.app
*.exe
*.dmg

# Jupyter
.ipynb_checkpoints/

# Ground truth test results
tests/ground_truth/results/
```

### 2.2 Create Root pyproject.toml

**File: `pyproject.toml`**

```toml
[project]
name = "itoa-agent"
version = "1.0.0"
description = "IT Operations AI Agent - Monorepo"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "Proprietary"}

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
strict = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]
ignore = ["E501"]
```

### 2.3 Create Requirements Files

**File: `requirements/base.txt`**

```txt
# Core
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Database
sqlalchemy>=2.0.0
asyncpg>=0.28.0
alembic>=1.11.0
psycopg2-binary>=2.9.0

# Cache & Queue
redis>=4.6.0
celery>=5.3.0

# HTTP Client
httpx>=0.24.0
aiohttp>=3.8.0

# Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.0
msal>=1.22.0

# LLM
langchain>=0.1.0
langchain-openai>=0.0.5
openai>=1.0.0

# Utilities
python-dotenv>=1.0.0
structlog>=23.1.0
tenacity>=8.2.0

# Desktop (optional - for desktop package)
# PySide6>=6.5.0
```

**File: `requirements/dev.txt`**

```txt
-r base.txt

# Code Quality
black>=23.0.0
isort>=5.12.0
ruff>=0.0.280
mypy>=1.4.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.24.0  # for TestClient

# Development
ipython>=8.14.0
watchdog>=3.0.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.1.0
```

**File: `requirements/test.txt`**

```txt
-r base.txt

pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-xdist>=3.3.0
httpx>=0.24.0
faker>=19.0.0
factory-boy>=3.3.0
```

---

## Step 3: Docker Configuration

### 3.1 Create docker-compose.yml

📝 **PROMPT: Generate Docker Compose for development**
```
Create a docker-compose.yml for local development with:
- PostgreSQL 15 with initialization scripts
- Redis 7
- 4 FastAPI services (auth, core, llm, action-worker)
- Shared network
- Volume mounts for hot reload
- Environment variables from .env file
```

**File: `docker-compose.yml`**

```yaml
version: '3.8'

services:
  # ===================
  # Infrastructure
  # ===================
  
  postgres:
    image: postgres:15-alpine
    container_name: itoa-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-itoa}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-itoa_dev_password}
      POSTGRES_DB: ${POSTGRES_DB:-itoa_db}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-itoa}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - itoa-network

  redis:
    image: redis:7-alpine
    container_name: itoa-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - itoa-network

  # ===================
  # Services
  # ===================

  auth-service:
    build:
      context: ./services/auth-service
      dockerfile: Dockerfile
    container_name: itoa-auth
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-itoa}:${POSTGRES_PASSWORD:-itoa_dev_password}@postgres:5432/${POSTGRES_DB:-itoa_db}
      - REDIS_URL=redis://redis:6379/0
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
      - AZURE_TENANT_ID=${AZURE_TENANT_ID}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-secret-key-change-in-production}
      - DEBUG=true
    ports:
      - "8001:8000"
    volumes:
      - ./services/auth-service/src:/app/src
      - ./shared/src:/app/shared
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - itoa-network

  core-service:
    build:
      context: ./services/core-service
      dockerfile: Dockerfile
    container_name: itoa-core
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-itoa}:${POSTGRES_PASSWORD:-itoa_dev_password}@postgres:5432/${POSTGRES_DB:-itoa_db}
      - REDIS_URL=redis://redis:6379/1
      - MECM_SERVER=${MECM_SERVER}
      - MECM_DATABASE=${MECM_DATABASE}
      - AUTH_SERVICE_URL=http://auth-service:8000
      - LLM_SERVICE_URL=http://llm-service:8000
      - DEBUG=true
    ports:
      - "8002:8000"
    volumes:
      - ./services/core-service/src:/app/src
      - ./shared/src:/app/shared
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - itoa-network

  llm-service:
    build:
      context: ./services/llm-service
      dockerfile: Dockerfile
    container_name: itoa-llm
    environment:
      - REDIS_URL=redis://redis:6379/2
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - LLM_PROVIDER=${LLM_PROVIDER:-openai}
      - DEBUG=true
    ports:
      - "8003:8000"
    volumes:
      - ./services/llm-service/src:/app/src
      - ./shared/src:/app/shared
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - itoa-network

  action-worker:
    build:
      context: ./services/action-worker
      dockerfile: Dockerfile
    container_name: itoa-worker
    command: celery -A action_worker.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-itoa}:${POSTGRES_PASSWORD:-itoa_dev_password}@postgres:5432/${POSTGRES_DB:-itoa_db}
      - REDIS_URL=redis://redis:6379/3
      - CELERY_BROKER_URL=redis://redis:6379/3
      - CELERY_RESULT_BACKEND=redis://redis:6379/3
      - SERVICENOW_INSTANCE=${SERVICENOW_INSTANCE}
      - SERVICENOW_USERNAME=${SERVICENOW_USERNAME}
      - SERVICENOW_PASSWORD=${SERVICENOW_PASSWORD}
      - TACHYON_URL=${TACHYON_URL}
      - TACHYON_API_KEY=${TACHYON_API_KEY}
    volumes:
      - ./services/action-worker/src:/app/src
      - ./shared/src:/app/shared
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - itoa-network

networks:
  itoa-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 3.2 Create .env.example

**File: `.env.example`**

```env
# Database
POSTGRES_USER=itoa
POSTGRES_PASSWORD=itoa_dev_password
POSTGRES_DB=itoa_db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60

# Azure AD OAuth
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id

# MECM
MECM_SERVER=your-mecm-server
MECM_DATABASE=CM_XXX
MECM_USERNAME=your-username
MECM_PASSWORD=your-password

# ServiceNow
SERVICENOW_INSTANCE=your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password

# 1E Tachyon
TACHYON_URL=https://your-tachyon-server
TACHYON_API_KEY=your-api-key

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key

# Azure OpenAI (alternative)
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Debug
DEBUG=true
LOG_LEVEL=INFO
```

---

## Step 4: Service Dockerfiles

### 4.1 Base Service Dockerfile Template

📝 **PROMPT: Generate FastAPI Dockerfile**
```
Create a production-ready Dockerfile for a FastAPI service with:
- Python 3.11 slim base
- Non-root user
- Multi-stage build for smaller image
- Health check
- Hot reload support for development
```

**File: `services/auth-service/Dockerfile`** (same pattern for all services)

```dockerfile
# ===================
# Build Stage
# ===================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ===================
# Production Stage
# ===================
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY src/ ./src/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File: `services/auth-service/requirements.txt`**

```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
asyncpg>=0.28.0
redis>=4.6.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.0
msal>=1.22.0
httpx>=0.24.0
structlog>=23.1.0
```

---

## Step 5: Development Setup Script

**File: `scripts/setup-dev.ps1`**

```powershell
#!/usr/bin/env pwsh

Write-Host "🚀 Setting up ITOA Agent Development Environment" -ForegroundColor Cyan

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Docker
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerVersion = docker --version
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Docker not found. Please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`n🐍 Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Gray
} else {
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n🔌 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements/dev.txt

# Install shared package in editable mode
Write-Host "`n📚 Installing shared package..." -ForegroundColor Yellow
pip install -e shared/

# Copy environment file
Write-Host "`n⚙️ Setting up environment file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file from template" -ForegroundColor Green
    Write-Host "⚠️  Please update .env with your credentials" -ForegroundColor Yellow
} else {
    Write-Host "Environment file already exists" -ForegroundColor Gray
}

# Start Docker services
Write-Host "`n🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d postgres redis

# Wait for services
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run database migrations
Write-Host "`n🗄️ Running database migrations..." -ForegroundColor Yellow
# alembic upgrade head

Write-Host "`n✅ Development environment setup complete!" -ForegroundColor Green
Write-Host @"

Next steps:
1. Update .env with your credentials
2. Start services: docker-compose up
3. Access services:
   - Auth Service: http://localhost:8001
   - Core Service: http://localhost:8002
   - LLM Service:  http://localhost:8003
   
Happy coding! 🎉
"@ -ForegroundColor Cyan
```

---

## Step 6: Verify Setup

### 6.1 Test Docker Compose

```powershell
# Start infrastructure only
docker-compose up -d postgres redis

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres
```

### 6.2 Test Database Connection

```powershell
# Connect to PostgreSQL
docker exec -it itoa-postgres psql -U itoa -d itoa_db

# Run a test query
\dt  # List tables (should be empty initially)
\q   # Quit
```

---

## Common Issues & Solutions

### Issue 1: Docker not starting

**Solution:**
```powershell
# Ensure Docker Desktop is running
# Restart Docker if needed
docker-compose down
docker-compose up -d
```

### Issue 2: Port already in use

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :5432

# Kill process or change port in docker-compose.yml
```

### Issue 3: Permission denied on volumes

**Solution:**
```powershell
# On Windows, ensure Docker Desktop has file sharing enabled
# Settings > Resources > File Sharing > Add your project folder
```

---

## Next Steps

Once project setup is complete, proceed to:
→ [02_Database_Schema.md](02_Database_Schema.md) - Set up PostgreSQL schema and models

---

**Checkpoint:** You should now have:
- [ ] Complete project folder structure
- [ ] Docker Compose configuration
- [ ] Environment file template
- [ ] Development setup script
- [ ] PostgreSQL and Redis running locally
