# Phase 201: Supervisord Configuration

## Objective

Create supervisord configurations for process management, logging, and MCP server group orchestration.

## Prerequisites

- Phase 200 completed
- Dockerfile setup done

## Steps

### 2.1: Create Supervisord Main Config

Create `docker/supervisor/supervisord.conf`:

```ini
[unix_http_server]
file=/var/run/supervisor.sock   ; (the path to the socket file)
chmod=0700                       ; sockef file mode (default 0700)

[supervisord]
logfile=/var/log/supervisor/supervisord.log ; (main log file;default $CWD/supervisord.log)
pidfile=/var/run/supervisord.pid             ; (supervisord pidfile;default supervisord.pid)
childlogdir=/var/log/supervisor              ; ('AUTO' child log dir, default $TEMP)
nodaemon=true                                ; (start in foreground if true;default false)
silent=false                                 ; (no logs to stdout if true;default false)
minprocs=200                                 ; (min. avail processes to allow changes)

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock ; use a unix:// URL  for a unix socket

[include]
files = /etc/supervisor/conf.d/*.conf
```

### 2.2: Create Supervisord Nginx Config

Create `docker/supervisor/nginx.conf`:

```ini
[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
directory=/etc/nginx
autostart=true
autorestart=unexpected
startsecs=1
startretries=3
priority=10
stopsignal=TERM
stopwaitsecs=10
stdout_logfile=/var/log/supervisor/nginx_stdout.log
stdout_logfile_maxbytes=50000000
stdout_logfile_backups=10
stderr_logfile=/var/log/supervisor/nginx_stderr.log
stderr_logfile_maxbytes=50000000
stderr_logfile_backups=10
redirect_stderr=false
environment=PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
numprocs=1
process_name=%(program_name)s
```

### 2.3: Create Supervisord Backend Config

Create `docker/supervisor/backend.conf`:

```ini
[program:backend]
command=/bin/bash -c "cd /app/backend && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001"
directory=/app/backend
autostart=true
autorestart=unexpected
startsecs=1
startretries=3
priority=20
stopsignal=TERM
stopwaitsecs=10
stdout_logfile=/var/log/supervisor/backend_stdout.log
stdout_logfile_maxbytes=50000000
stdout_logfile_backups=10
stderr_logfile=/var/log/supervisor/backend_stderr.log
stderr_logfile_maxbytes=50000000
stderr_logfile_backups=10
redirect_stderr=false
environment=PATH="/root/.local/share/mise/shims:/root/.local/share/mise/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin",PYTHONUNBUFFERED=1,PYTHONPATH=/app/backend/src
numprocs=1
process_name=%(program_name)s
```

### 2.4: Create MCP Group Supervisord Config

Create `docker/supervisor/mcp_group.conf`:

```ini
[group:mcp_servers]
priority=999
programs=
; Programs added dynamically via sync_processes endpoint
; Format: mcp_{server_name}
```

### 2.5: Create Logrotate Configuration

Create `docker/logrotate/supervisord`:

```
/var/log/supervisor/*.log {
    daily
    rotate 10
    missingok
    notifempty
    compress
    delaycompress
    postrotate
        /usr/lib/supervisor/supervisorctl -c /etc/supervisor/supervisord.conf reread >/dev/null 2>&1 || true
        /usr/lib/supervisor/supervisorctl -c /etc/supervisor/supervisord.conf update >/dev/null 2>&1 || true
    endscript
}
```

Install in Docker:

```dockerfile
# In Dockerfile, add to base stage:
COPY docker/logrotate/supervisord /etc/logrotate.d/supervisord
RUN chmod 644 /etc/logrotate.d/supervisord

# Install cron to run logrotate
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Add logrotate to crontab
RUN echo "0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/supervisord" | crontab -
```

---

## Directory Structure

```
docker/
├── supervisor/
│   ├── supervisord.conf    # Main supervisord config
│   ├── nginx.conf          # Nginx process config
│   ├── backend.conf        # Backend process config
│   └── mcp_group.conf      # MCP servers group
└── logrotate/
    └── supervisord         # Logrotate config for supervisor logs
```

## Verification Checklist

- [ ] `docker/supervisor/supervisord.conf` created
- [ ] `docker/supervisor/nginx.conf` created
- [ ] `docker/supervisor/backend.conf` created
- [ ] `docker/supervisor/mcp_group.conf` created
- [ ] `docker/logrotate/supervisord` created
- [ ] Logrotate installation in Dockerfile
- [ ] All process configs have proper logging
- [ ] Supervisor group configured for MCP servers

## Next Step

Proceed to [202-entrypoint-and-nginx.md](./202-entrypoint-and-nginx.md)
