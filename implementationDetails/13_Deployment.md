# 13 - Deployment Guide

## Overview

This guide covers deploying the IT Operations AI Agent to production environments using Docker, Kubernetes, and CI/CD pipelines. It includes configuration for development, staging, and production environments.

---

## Prerequisites

- Docker Desktop installed
- kubectl configured for your Kubernetes cluster
- Container registry access (Docker Hub, ACR, or ECR)
- All services implemented and tested locally

---

## Step 1: Docker Configuration

### Service Dockerfiles

📝 **PROMPT: Create Dockerfile for FastAPI service**
```
Create a production-ready Dockerfile for the core service:
- Multi-stage build for smaller image
- Non-root user for security
- Health check configuration
```

**File: `services/core-service/Dockerfile`**

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

CMD ["uvicorn", "core_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**File: `services/core-service/requirements.txt`**

```text
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.28.0
alembic>=1.11.0
python-jose[cryptography]>=3.3.0
msal>=1.22.0
httpx>=0.24.0
redis>=4.6.0
structlog>=23.1.0
tenacity>=8.2.0
```

### Desktop App Dockerfile

**File: `desktop/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Qt dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libxkbcommon0 \
    libdbus-1-3 \
    libegl1 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY resources/ ./resources/

ENV PYTHONPATH=/app/src
ENV QT_QPA_PLATFORM=offscreen

CMD ["python", "-m", "desktop_app.main"]
```

---

## Step 2: Docker Compose

📝 **PROMPT: Create Docker Compose for local development**
```
Create a Docker Compose configuration that:
- Runs all services locally
- Includes PostgreSQL and Redis
- Sets up networking between services
- Supports hot reload for development
```

**File: `docker-compose.yml`**

```yaml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: itops_agent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Core Service
  core-service:
    build:
      context: ./services/core-service
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/itops_agent
      REDIS_URL: redis://redis:6379/0
      DEBUG: "true"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./services/core-service/src:/app/src
    command: uvicorn core_service.main:app --host 0.0.0.0 --port 8001 --reload

  # Auth Service
  auth-service:
    build:
      context: ./services/auth-service
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/itops_agent
      REDIS_URL: redis://redis:6379/0
      AZURE_AD_TENANT_ID: ${AZURE_AD_TENANT_ID}
      AZURE_AD_CLIENT_ID: ${AZURE_AD_CLIENT_ID}
      AZURE_AD_CLIENT_SECRET: ${AZURE_AD_CLIENT_SECRET}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./services/auth-service/src:/app/src

  # MECM Connector
  mecm-connector:
    build:
      context: ./services/mecm-connector
      dockerfile: Dockerfile
    ports:
      - "8003:8003"
    environment:
      MECM_SERVER: ${MECM_SERVER}
      MECM_DATABASE: ${MECM_DATABASE}
      REDIS_URL: redis://redis:6379/1
    depends_on:
      - redis
    volumes:
      - ./services/mecm-connector/src:/app/src

  # ServiceNow Connector
  servicenow-connector:
    build:
      context: ./services/servicenow-connector
      dockerfile: Dockerfile
    ports:
      - "8004:8004"
    environment:
      SNOW_INSTANCE_URL: ${SNOW_INSTANCE_URL}
      SNOW_USERNAME: ${SNOW_USERNAME}
      SNOW_PASSWORD: ${SNOW_PASSWORD}
    volumes:
      - ./services/servicenow-connector/src:/app/src

  # Tachyon Connector
  tachyon-connector:
    build:
      context: ./services/tachyon-connector
      dockerfile: Dockerfile
    ports:
      - "8005:8005"
    environment:
      TACHYON_PLATFORM_URL: ${TACHYON_PLATFORM_URL}
      TACHYON_CERT_PATH: /certs/client.pem
      TACHYON_KEY_PATH: /certs/client-key.pem
    volumes:
      - ./services/tachyon-connector/src:/app/src
      - ./certs:/certs:ro

  # LLM Service
  llm-service:
    build:
      context: ./services/llm-service
      dockerfile: Dockerfile
    ports:
      - "8007:8007"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY}
      AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT}
    volumes:
      - ./services/llm-service/src:/app/src

  # Action Worker
  action-worker:
    build:
      context: ./services/action-worker
      dockerfile: Dockerfile
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/itops_agent
      CORE_SERVICE_URL: http://core-service:8001
      SERVICENOW_CONNECTOR_URL: http://servicenow-connector:8004
      TACHYON_CONNECTOR_URL: http://tachyon-connector:8005
    depends_on:
      - postgres
      - redis
    command: celery -A action_worker.celery_app worker --loglevel=info

  # Action Worker API
  action-worker-api:
    build:
      context: ./services/action-worker
      dockerfile: Dockerfile
    ports:
      - "8006:8006"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/itops_agent
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: uvicorn action_worker.api:app --host 0.0.0.0 --port 8006 --reload

  # Celery Beat
  celery-beat:
    build:
      context: ./services/action-worker
      dockerfile: Dockerfile
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - redis
    command: celery -A action_worker.celery_app beat --loglevel=info

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: itops-network
```

---

## Step 3: Kubernetes Deployment

📝 **PROMPT: Create Kubernetes manifests**
```
Create Kubernetes manifests for production deployment:
- Deployments with resource limits
- Services and ingress
- ConfigMaps and Secrets
- Horizontal Pod Autoscaler
```

### Namespace and ConfigMap

**File: `k8s/base/namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: itops-agent
  labels:
    app.kubernetes.io/name: itops-agent
```

**File: `k8s/base/configmap.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: itops-config
  namespace: itops-agent
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  CORE_SERVICE_URL: "http://core-service:8001"
  AUTH_SERVICE_URL: "http://auth-service:8002"
  MECM_CONNECTOR_URL: "http://mecm-connector:8003"
  SERVICENOW_CONNECTOR_URL: "http://servicenow-connector:8004"
  TACHYON_CONNECTOR_URL: "http://tachyon-connector:8005"
  ACTION_WORKER_URL: "http://action-worker-api:8006"
  LLM_SERVICE_URL: "http://llm-service:8007"
```

### Secrets Template

**File: `k8s/base/secrets.yaml`**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: itops-secrets
  namespace: itops-agent
type: Opaque
stringData:
  # Database
  DATABASE_URL: "postgresql+asyncpg://user:password@postgres:5432/itops_agent"
  
  # Redis
  REDIS_URL: "redis://:password@redis:6379/0"
  
  # Azure AD
  AZURE_AD_TENANT_ID: "<tenant-id>"
  AZURE_AD_CLIENT_ID: "<client-id>"
  AZURE_AD_CLIENT_SECRET: "<client-secret>"
  
  # ServiceNow
  SNOW_INSTANCE_URL: "https://company.service-now.com"
  SNOW_USERNAME: "<username>"
  SNOW_PASSWORD: "<password>"
  
  # LLM
  OPENAI_API_KEY: "<api-key>"
  AZURE_OPENAI_API_KEY: "<api-key>"
  AZURE_OPENAI_ENDPOINT: "<endpoint>"
  
  # JWT
  JWT_SECRET_KEY: "<secret-key>"
```

### Core Service Deployment

**File: `k8s/services/core-service.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: core-service
  namespace: itops-agent
  labels:
    app: core-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: core-service
  template:
    metadata:
      labels:
        app: core-service
    spec:
      containers:
        - name: core-service
          image: registry.company.com/itops-agent/core-service:latest
          ports:
            - containerPort: 8001
          envFrom:
            - configMapRef:
                name: itops-config
            - secretRef:
                name: itops-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 5
            periodSeconds: 10
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true
---
apiVersion: v1
kind: Service
metadata:
  name: core-service
  namespace: itops-agent
spec:
  selector:
    app: core-service
  ports:
    - port: 8001
      targetPort: 8001
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: core-service-hpa
  namespace: itops-agent
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: core-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Action Worker Deployment

**File: `k8s/services/action-worker.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: action-worker
  namespace: itops-agent
  labels:
    app: action-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: action-worker
  template:
    metadata:
      labels:
        app: action-worker
    spec:
      containers:
        - name: action-worker
          image: registry.company.com/itops-agent/action-worker:latest
          command: ["celery", "-A", "action_worker.celery_app", "worker", "--loglevel=info"]
          envFrom:
            - configMapRef:
                name: itops-config
            - secretRef:
                name: itops-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-beat
  namespace: itops-agent
  labels:
    app: celery-beat
spec:
  replicas: 1  # Only one beat scheduler
  selector:
    matchLabels:
      app: celery-beat
  template:
    metadata:
      labels:
        app: celery-beat
    spec:
      containers:
        - name: celery-beat
          image: registry.company.com/itops-agent/action-worker:latest
          command: ["celery", "-A", "action_worker.celery_app", "beat", "--loglevel=info"]
          envFrom:
            - configMapRef:
                name: itops-config
            - secretRef:
                name: itops-secrets
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
```

### Ingress Configuration

**File: `k8s/ingress/ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: itops-ingress
  namespace: itops-agent
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  tls:
    - hosts:
        - itops-api.company.com
      secretName: itops-tls
  rules:
    - host: itops-api.company.com
      http:
        paths:
          - path: /api/v1/rules
            pathType: Prefix
            backend:
              service:
                name: core-service
                port:
                  number: 8001
          - path: /api/v1/scans
            pathType: Prefix
            backend:
              service:
                name: core-service
                port:
                  number: 8001
          - path: /api/v1/auth
            pathType: Prefix
            backend:
              service:
                name: auth-service
                port:
                  number: 8002
          - path: /api/v1/actions
            pathType: Prefix
            backend:
              service:
                name: action-worker-api
                port:
                  number: 8006
          - path: /api/v1/llm
            pathType: Prefix
            backend:
              service:
                name: llm-service
                port:
                  number: 8007
```

---

## Step 4: CI/CD Pipeline

📝 **PROMPT: Create GitHub Actions CI/CD pipeline**
```
Create a GitHub Actions workflow that:
- Builds and tests all services
- Runs linting and security scans
- Builds Docker images
- Deploys to Kubernetes
```

**File: `.github/workflows/ci-cd.yaml`**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: registry.company.com
  IMAGE_PREFIX: itops-agent

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install ruff mypy
      
      - name: Run Ruff
        run: ruff check .
      
      - name: Run MyPy
        run: mypy services/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio pytest-cov
          pip install -r services/core-service/requirements.txt
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/ --cov=services --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'

  build:
    needs: [lint, test, security-scan]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    strategy:
      matrix:
        service:
          - core-service
          - auth-service
          - mecm-connector
          - servicenow-connector
          - tachyon-connector
          - llm-service
          - action-worker
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./services/${{ matrix.service }}
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig
      
      - name: Deploy to staging
        run: |
          kubectl apply -f k8s/base/
          kubectl apply -f k8s/services/
          kubectl set image deployment/core-service \
            core-service=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/core-service:${{ github.sha }} \
            -n itops-agent
          kubectl rollout status deployment/core-service -n itops-agent

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG_PROD }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig
      
      - name: Deploy to production
        run: |
          kubectl apply -f k8s/base/
          kubectl apply -f k8s/services/
          kubectl apply -f k8s/ingress/
          
          # Rolling update all services
          for service in core-service auth-service mecm-connector servicenow-connector tachyon-connector llm-service action-worker; do
            kubectl set image deployment/$service \
              $service=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/$service:${{ github.sha }} \
              -n itops-agent
          done
          
          # Wait for rollouts
          kubectl rollout status deployment -n itops-agent --timeout=600s
```

---

## Step 5: Database Migrations

**File: `scripts/run-migrations.sh`**

```bash
#!/bin/bash
set -e

echo "Running database migrations..."

cd services/core-service
alembic upgrade head

echo "Migrations complete!"
```

**File: `k8s/jobs/migration-job.yaml`**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: itops-agent
spec:
  template:
    spec:
      containers:
        - name: migration
          image: registry.company.com/itops-agent/core-service:latest
          command: ["alembic", "upgrade", "head"]
          envFrom:
            - secretRef:
                name: itops-secrets
      restartPolicy: OnFailure
  backoffLimit: 3
```

---

## Step 6: Monitoring and Observability

**File: `k8s/monitoring/prometheus-servicemonitor.yaml`**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: itops-services
  namespace: itops-agent
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      monitoring: enabled
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

**File: `k8s/monitoring/grafana-dashboard.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: itops-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  itops-dashboard.json: |
    {
      "dashboard": {
        "title": "IT Operations AI Agent",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(http_requests_total{namespace=\"itops-agent\"}[5m])) by (service)"
              }
            ]
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(http_requests_total{namespace=\"itops-agent\",status=~\"5..\"}[5m])) by (service)"
              }
            ]
          },
          {
            "title": "Action Queue Length",
            "type": "stat",
            "targets": [
              {
                "expr": "celery_queue_length{queue=\"default\"}"
              }
            ]
          }
        ]
      }
    }
```

---

## Step 7: Desktop App Distribution (Cross-Platform)

📝 **PROMPT: Create desktop app build and distribution**
```
Create scripts for building and distributing the desktop application:
- PyInstaller configuration for Windows and macOS
- MSI installer for Windows
- DMG installer for macOS
- Code signing and notarization
```

### PyInstaller Spec (Cross-Platform)

**File: `desktop/build.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import platform

block_cipher = None

# Platform-specific settings
is_windows = sys.platform == 'win32'
is_macos = sys.platform == 'darwin'

icon_file = 'resources/icons/app.ico' if is_windows else 'resources/icons/app.icns'

a = Analysis(
    ['src/desktop_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('src/desktop_app/styles', 'desktop_app/styles'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if is_macos:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ITOpsAgent',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon=icon_file,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='ITOpsAgent',
    )
    app = BUNDLE(
        coll,
        name='ITOpsAgent.app',
        icon=icon_file,
        bundle_identifier='com.company.itopsagent',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '12.0',
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='ITOpsAgent',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_file,
    )
```

### Windows Build Script

**File: `desktop/build-windows.ps1`**

```powershell
# Build desktop application for Windows

Write-Host "Building IT Operations AI Agent Desktop (Windows)..."

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install pyinstaller

# Build executable
pyinstaller build.spec --clean

# Code sign the executable (requires certificate)
if (Test-Path "cert\code-signing.pfx") {
    $certPassword = Read-Host -AsSecureString "Enter certificate password"
    & signtool sign /f "cert\code-signing.pfx" /p $certPassword /tr http://timestamp.digicert.com /td sha256 "dist\ITOpsAgent.exe"
}

# Create installer (requires WiX Toolset)
& "C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe" installer.wxs
& "C:\Program Files (x86)\WiX Toolset v3.11\bin\light.exe" installer.wixobj -o "dist\ITOpsAgent-Setup.msi"

# Sign the MSI
if (Test-Path "cert\code-signing.pfx") {
    & signtool sign /f "cert\code-signing.pfx" /p $certPassword /tr http://timestamp.digicert.com /td sha256 "dist\ITOpsAgent-Setup.msi"
}

Write-Host "Build complete! Output: dist\ITOpsAgent-Setup.msi"
```

### macOS Build Script

**File: `desktop/build-macos.sh`**

```bash
#!/bin/bash
set -e

echo "Building IT Operations AI Agent Desktop (macOS)..."

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install pyinstaller

# Build .app bundle
pyinstaller build.spec --clean

# Code sign the app (requires Apple Developer certificate)
IDENTITY="Developer ID Application: Your Company (TEAMID)"
APP_PATH="dist/ITOpsAgent.app"

if security find-identity -v -p codesigning | grep -q "$IDENTITY"; then
    echo "Signing application..."
    codesign --deep --force --verify --verbose \
        --sign "$IDENTITY" \
        --options runtime \
        --entitlements entitlements.plist \
        "$APP_PATH"
    
    # Verify signature
    codesign --verify --verbose "$APP_PATH"
else
    echo "Warning: Code signing identity not found. Skipping signing."
fi

# Create DMG
echo "Creating DMG..."
DMG_NAME="ITOpsAgent-1.0.0.dmg"

# Create temporary DMG folder
mkdir -p dist/dmg
cp -R "$APP_PATH" dist/dmg/
ln -s /Applications dist/dmg/Applications

# Create DMG
hdiutil create -volname "IT Ops Agent" \
    -srcfolder dist/dmg \
    -ov -format UDZO \
    "dist/$DMG_NAME"

# Sign DMG
if security find-identity -v -p codesigning | grep -q "$IDENTITY"; then
    codesign --sign "$IDENTITY" "dist/$DMG_NAME"
fi

# Cleanup
rm -rf dist/dmg

echo "Build complete! Output: dist/$DMG_NAME"

# Notarization (requires Apple Developer account)
echo ""
echo "To notarize the DMG, run:"
echo "xcrun notarytool submit dist/$DMG_NAME --apple-id YOUR_APPLE_ID --team-id TEAM_ID --password APP_SPECIFIC_PASSWORD --wait"
echo "xcrun stapler staple dist/$DMG_NAME"
```

### macOS Entitlements

**File: `desktop/entitlements.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <false/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <false/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
```

### GitHub Actions: Desktop Build Pipeline

**File: `.github/workflows/desktop-build.yaml`**

```yaml
name: Desktop App Build

on:
  push:
    tags:
      - 'desktop-v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd desktop
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executable
        run: |
          cd desktop
          pyinstaller build.spec --clean
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: windows-build
          path: desktop/dist/ITOpsAgent.exe

  build-macos-intel:
    runs-on: macos-13  # Intel runner
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd desktop
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build app bundle
        run: |
          cd desktop
          pyinstaller build.spec --clean
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: macos-intel-build
          path: desktop/dist/ITOpsAgent.app

  build-macos-arm:
    runs-on: macos-14  # Apple Silicon runner
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd desktop
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build app bundle
        run: |
          cd desktop
          pyinstaller build.spec --clean
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: macos-arm-build
          path: desktop/dist/ITOpsAgent.app

  create-release:
    needs: [build-windows, build-macos-intel, build-macos-arm]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            windows-build/ITOpsAgent.exe
            macos-intel-build/ITOpsAgent.app
            macos-arm-build/ITOpsAgent.app
```

---

## Verification Checklist

### Local Development

```powershell
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f core-service

# Run database migrations
docker-compose exec core-service alembic upgrade head

# Test API
curl http://localhost:8001/health
```

### Kubernetes Deployment

```powershell
# Apply configurations
kubectl apply -f k8s/base/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/

# Check pods
kubectl get pods -n itops-agent

# View logs
kubectl logs -f deployment/core-service -n itops-agent

# Check ingress
kubectl get ingress -n itops-agent
```

---

## Common Issues

### Issue: Pod CrashLoopBackOff

**Solution:** Check logs with `kubectl logs` and verify secrets are configured correctly

### Issue: Database connection timeout

**Solution:** Verify network policies allow pod-to-database communication

### Issue: Image pull errors

**Solution:** Ensure container registry credentials are configured in Kubernetes secrets

---

## Production Checklist

- [ ] All secrets stored in secure secret management (Azure Key Vault, HashiCorp Vault)
- [ ] TLS certificates configured for all external endpoints
- [ ] Network policies restrict pod-to-pod communication
- [ ] Resource limits set for all deployments
- [ ] Horizontal Pod Autoscaler configured
- [ ] Monitoring and alerting configured
- [ ] Backup strategy for PostgreSQL implemented
- [ ] Disaster recovery plan documented
- [ ] Security scanning in CI/CD pipeline
- [ ] Log aggregation configured (ELK/Loki)
- [ ] Desktop app tested on Windows 10/11
- [ ] Desktop app tested on macOS (Intel and Apple Silicon)
- [ ] Windows installer signed with code signing certificate
- [ ] macOS app notarized with Apple

---

**Checkpoint:** You should now have:
- [ ] All services containerized
- [ ] Docker Compose working locally
- [ ] Kubernetes manifests applied
- [ ] CI/CD pipeline deploying successfully
- [ ] Desktop app building for Windows and macOS
- [ ] Monitoring dashboards available
