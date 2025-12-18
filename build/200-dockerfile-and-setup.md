# Phase 200: Dockerfile and Base Container Setup

## Objective

Create Dockerfile with multi-stage build and base container configuration for containerization.

## Prerequisites

- Phase 030-110 completed
- Backend code ready
- Frontend built (`frontend/dist/` exists)
- Docker installed

## Critical Requirements

- TinyDB must persist via `/app/data` Docker volume
- Process logs handled by logrotate in `/var/log/supervisor/` — no persistence in DB
- No healthchecks on individual processes
- APP_USERNAME and APP_PASSWORD **REQUIRED** — no defaults
- Sync Processes button is the ONLY way to write configs to disk

## Steps

### 2.1: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# Multi-stage build
FROM python:3.10-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    unzip \
    ca-certificates \
    openssl \
    build-essential \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install mise (for dependency management in container)
RUN curl https://mise.jdx.dev/install.sh | sh

# Set environment for mise
ENV PATH="/root/.local/share/mise/shims:/root/.local/share/mise/bin:$PATH"
ENV APP_ENV=production

WORKDIR /app

# Copy project files
COPY backend/ /app/backend/
COPY frontend/dist/ /app/frontend/dist/
COPY docker/ /app/docker/
COPY .env /app/.env

# Install Python dependencies (using UV directly, not MISE)
RUN cd /app/backend && pip install uv && uv sync --frozen

# Generate self-signed SSL certificate
RUN mkdir -p /etc/ssl/private && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/server.key \
    -out /etc/ssl/certs/server.crt \
    -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"

# Create data directory for TinyDB persistence
RUN mkdir -p /app/data && chmod 755 /app/data

# Create servers directory for MCP server configs (written by sync process)
RUN mkdir -p /app/servers && chmod 755 /app/servers

# Create log directory
RUN mkdir -p /var/log/supervisor && chmod 755 /var/log/supervisor

# Copy entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 443 8001 8100-8999

# No healthchecks: processes are managed by supervisord
# Logs are handled by supervisord logrotate in /var/log/supervisor/

ENTRYPOINT ["/entrypoint.sh"]
```

**Volumes**:
- `/app/data` — TinyDB database (must persist across container restarts)
- `/app/servers` — MCP server configs (written by sync endpoint)
- `/var/log/supervisor/` — Process logs (handled by logrotate, ephemeral)

### 2.2: Create .dockerignore

Create `.dockerignore` in project root:

```
# Version control
.git
.gitignore

# Node
node_modules/
frontend/node_modules/
npm-debug.log
yarn-error.log

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.venv/
venv/
.pytest_cache/
.coverage

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Build outputs
frontend/dist/old
backend/build/
backend/dist/

# Environment
.env.local
.env.test
*.key

# Documentation
docs/
README.md

# Temporary
tmp/
temp/
```

---

## Verification Checklist

- [ ] `Dockerfile` created
- [ ] `.dockerignore` created
- [ ] All required directories created in Dockerfile
- [ ] SSL certificate generation configured
- [ ] Python dependencies installed
- [ ] Ports 443, 8001, 8100-8999 exposed
- [ ] Entrypoint script configured

## Next Step

Proceed to [201-supervisor-configuration.md](./201-supervisor-configuration.md)
