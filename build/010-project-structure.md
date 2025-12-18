# Phase 1: Project Structure & Dependencies

## Objective

Set up the complete directory structure, initialize Python and Node.js projects, and configure environment files.

## Prerequisites

- Python 3.10+ installed
- Node.js 20+ installed
- `uv` package manager installed
- Docker installed
- Text editor or IDE

## Steps

### 1.1: Create Root Directory Structure

```bash
cd /Users/daniel/projects/mcpzoo

# Create main directories
mkdir -p backend frontend docker/{supervisor,nginx} docs

# Create volume mount directory
mkdir -p docker/data

# Add .gitkeep to persist empty directories
touch docker/data/.gitkeep
```

**Verify:**
```bash
ls -la
# Should show: backend/, frontend/, docker/, docs/, and existing files
```

---

### 1.2: Create Backend Project Structure

```bash
cd backend

# Create Python package structure
mkdir -p src/backend/{routers,utils} tests

# Create initial files
touch src/backend/__init__.py
touch src/backend/main.py
touch src/backend/settings.py
touch src/backend/auth.py
touch src/backend/tinydb.py
touch src/backend/models.py
touch src/backend/supervisor_api.py
touch src/backend/routers/__init__.py
touch src/backend/routers/auth.py
touch src/backend/routers/servers.py
touch src/backend/routers/software.py
touch src/backend/routers/processes.py
touch src/backend/utils/__init__.py
touch src/backend/utils/logging.py
touch src/backend/utils/shell.py
touch tests/__init__.py

cd ..
```

**Verify:**
```bash
find backend -type f -name "*.py" | wc -l
# Should output: 15 Python files
```

---

### 1.3: Create Backend pyproject.toml

Create `backend/pyproject.toml`:

```toml
[project]
name = "mcpzoo-backend"
version = "0.1.0"
description = "MCPZoo Backend - MCP Server Management"
requires-python = ">=3.10"
authors = [{name = "MCPZoo Team"}]

dependencies = [
    "fastapi==0.109.0",
    "uvicorn==0.27.0",
    "pydantic==2.5.0",
    "pydantic-settings==2.1.0",
    "tinydb==4.8.0",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.6",
    "httpx==0.25.2",
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.3",
    "pytest-asyncio==0.21.1",
    "pytest-cov==4.1.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

**Verify:**
```bash
cd backend && uv sync && cd ..
# Should install all dependencies without errors
```

---

### 1.4: Backend Directory Structure Complete

Backend structure is now complete. All files are in place for Phase 2.

### 1.5: Create Frontend Project Structure

```bash
cd frontend

# Create directory structure
mkdir -p public src/{components,pages,hooks,context,api,styles}

# Create initial files
touch public/index.html
touch src/main.tsx
touch src/App.tsx
touch src/styles/style.css
touch src/components/.gitkeep
touch src/pages/.gitkeep
touch src/hooks/.gitkeep
touch src/context/.gitkeep
touch src/api/.gitkeep

cd ..
```

**Verify:**
```bash
find frontend/src -type f | wc -l
# Should output: 8+ files
```

---

### 1.6: Create Frontend package.json

Create `frontend/package.json`:

```json
{
  "name": "mcpzoo-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.3",
    "vite": "^5.0.8",
    "vitest": "^1.0.4"
  }
}
```

---

### 1.7: Create Frontend tsconfig.json

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "resolveJsonModule": true,
    "moduleResolution": "bundler"
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

---

### 1.8: Create Frontend vite.config.ts

Create `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://localhost:8001',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  }
})
```

---

### 1.9: Create .env.example

Create `.env.example` in project root:

```bash
# Application
APP_USERNAME=admin
APP_PASSWORD=changeme123

# Database
TINYDB_PATH=/app/data/tinydb.json

# JWT
JWT_SECRET=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Server Ports (internal)
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8001
NGINX_PORT=443

# MCP Server Port Range
MCP_PORT_MIN=8100
MCP_PORT_MAX=8999

# Logging
LOG_LEVEL=INFO
```

---

### 1.10: Create .env (for local development)

```bash
cp .env.example .env
# Edit .env and update JWT_SECRET with a random value
```

---

### 1.11: Create .gitignore

Create `.gitignore` in project root:

```
# Environment
.env
.env.local

# Python
backend/.venv/
backend/__pycache__/
backend/*.pyc
backend/dist/
backend/build/
backend/*.egg-info/
backend/.pytest_cache/

# Node
frontend/node_modules/
frontend/dist/
frontend/build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Logs
*.log
logs/
docker/data/tinydb.json
```

---

## Verification Checklist

After completing Phase 1:

- [ ] Root directory has `backend/`, `frontend/`, `docker/`, `docs/` directories
- [ ] `backend/src/backend/` has all required Python files
- [ ] `backend/pyproject.toml` exists and `uv sync` succeeds
- [ ] `frontend/package.json` exists
- [ ] `frontend/tsconfig.json` exists
- [ ] `frontend/vite.config.ts` exists
- [ ] `.env.example` created and `.env` copied
- [ ] `.gitignore` exists

## Next Step

Once verified, proceed to [Phase 2: Backend Implementation](./02-backend-implementation.md)
