# Phase 202: Entrypoint and Nginx Configuration

## Objective

Create entrypoint script, Nginx configuration, docker-compose file, and verification procedures.

## Prerequisites

- Phase 200-201 completed
- Supervisord configs created

## Steps

### 2.1: Create Entrypoint Script

Create `docker/entrypoint.sh`:

```bash
#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}MCPZoo Container Starting...${NC}"

# Check required environment variables
if [ -z "$APP_USERNAME" ]; then
    echo -e "${RED}ERROR: APP_USERNAME not set${NC}"
    exit 1
fi

if [ -z "$APP_PASSWORD" ]; then
    echo -e "${RED}ERROR: APP_PASSWORD not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Credentials configured${NC}"

# Ensure data directory exists and is writable
mkdir -p /app/data
chmod 755 /app/data

# Ensure servers directory exists and is writable
mkdir -p /app/servers
chmod 755 /app/servers

# Ensure log directory exists
mkdir -p /var/log/supervisor
chmod 755 /var/log/supervisor

echo -e "${GREEN}✓ Directories prepared${NC}"

# Start supervisord in foreground
echo -e "${GREEN}Starting supervisord...${NC}"
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
```

Make executable:
```bash
chmod +x docker/entrypoint.sh
```

### 2.2: Create Nginx Configuration

Create `docker/nginx/default.conf`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name _;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/server.crt;
    ssl_certificate_key /etc/ssl/private/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Root location - serve frontend
    location / {
        root /app/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8001;
        access_log off;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ ~$ {
        deny all;
    }
}
```

### 2.3: Create docker-compose.yml (Development/Testing)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  mcpzoo:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mcpzoo
    ports:
      - "443:443"
      - "8001:8001"
      - "8100-8999:8100-8999"
    environment:
      APP_USERNAME: admin
      APP_PASSWORD: changeme123
      JWT_SECRET: dev-secret-key
      TINYDB_PATH: /app/data/tinydb.json
      LOG_LEVEL: INFO
    volumes:
      - mcpzoo-data:/app/data
      - mcpzoo-servers:/app/servers
      - mcpzoo-logs:/var/log/supervisor
    restart: unless-stopped
    networks:
      - mcpzoo-net

volumes:
  mcpzoo-data:
    driver: local
  mcpzoo-servers:
    driver: local
  mcpzoo-logs:
    driver: local

networks:
  mcpzoo-net:
    driver: bridge
```

### 2.4: Create Directory Structure Script

Create `docker/setup.sh` to ensure all directories exist:

```bash
#!/bin/bash
mkdir -p docker/supervisor
mkdir -p docker/nginx
mkdir -p docker/logrotate
echo "Docker directory structure created"
```

---

## Verification Procedures

### 2.1: Verify Directory Structure

```bash
tree docker/
# Output should show:
# docker/
# ├── supervisor/
# │   ├── supervisord.conf
# │   ├── nginx.conf
# │   ├── backend.conf
# │   └── mcp_group.conf
# ├── nginx/
# │   └── default.conf
# ├── logrotate/
# │   └── supervisord
# ├── entrypoint.sh
# └── setup.sh
```

### 2.2: Build Docker Image

```bash
docker build -t mcpzoo:latest .
```

Verify build output:
```bash
docker images | grep mcpzoo
# Should show: mcpzoo  latest  <image-id>  <time>
```

### 2.3: Test Container Startup (Dry Run)

```bash
docker-compose up --build
```

Expected output:
```
mcpzoo | MCPZoo Container Starting...
mcpzoo | ✓ Credentials configured
mcpzoo | ✓ Directories prepared
mcpzoo | Starting supervisord...
mcpzoo | supervisord started with pid 1
mcpzoo | spawned: 'nginx' with pid ...
mcpzoo | spawned: 'backend' with pid ...
mcpzoo | entered RUNNING state
```

### 2.4: Verify Running Processes

```bash
docker exec mcpzoo supervisorctl status
```

Expected output:
```
backend                          RUNNING   pid 12, uptime 0:00:05
nginx                            RUNNING   pid 11, uptime 0:00:05
```

### 2.5: Test API Endpoint

```bash
# Should work (SSL warning expected with self-signed cert)
curl -k https://localhost/health
# Expected response: {"status": "healthy"}

curl -k -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme123"}'
# Expected response: {"access_token": "..."}
```

### 2.6: Test Frontend

Open browser: `https://localhost`
- Should load MCPZoo login page
- Can login with credentials

### 2.7: Verify Data Persistence

```bash
# Create a test file in container
docker exec mcpzoo bash -c "echo 'test' > /app/data/test.txt"

# Stop and remove container
docker-compose down

# Start again
docker-compose up -d

# Verify file still exists
docker exec mcpzoo cat /app/data/test.txt
# Should output: test
```

---

## Critical Verification Checklist

- [ ] `docker/entrypoint.sh` created and executable
- [ ] `docker/nginx/default.conf` created
- [ ] `docker-compose.yml` created
- [ ] Docker image builds successfully
- [ ] Container starts without errors
- [ ] supervisord runs in foreground
- [ ] Nginx process running
- [ ] Backend API responding
- [ ] Frontend loads in browser
- [ ] TinyDB data persists after restart
- [ ] Credentials required (no defaults)
- [ ] SSL certificate generated
- [ ] Logs accessible in /var/log/supervisor/

## Environment Variables

Required:
- `APP_USERNAME` - Login username (REQUIRED, no default)
- `APP_PASSWORD` - Login password (REQUIRED, no default)

Optional:
- `JWT_SECRET` - JWT signing key (default: dev-secret-key)
- `TINYDB_PATH` - Database file path (default: /app/data/tinydb.json)
- `LOG_LEVEL` - Logging level (default: INFO)
- `FASTAPI_HOST` - API host (default: 0.0.0.0)
- `FASTAPI_PORT` - API port (default: 8001)

## Port Mapping

- **443** - HTTPS frontend and API
- **8001** - Backend FastAPI (internal, proxied by Nginx)
- **8100-8999** - MCP server ports (for external clients)

## Volumes

- `/app/data` - TinyDB database (persist)
- `/app/servers` - MCP server configurations (persist)
- `/var/log/supervisor/` - Process logs (optional persist)

## Next Step

Once verified, proceed to [300-integration-and-docs.md](./300-integration-and-docs.md)
