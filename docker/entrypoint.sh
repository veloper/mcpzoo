#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}MCPZoo Container Starting...${NC}"

if [ -z "$APP_USERNAME" ]; then
    echo -e "${RED}ERROR: APP_USERNAME not set${NC}"
    exit 1
fi

if [ -z "$APP_PASSWORD" ]; then
    echo -e "${RED}ERROR: APP_PASSWORD not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Credentials configured${NC}"

mkdir -p /app/data
chmod 755 /app/data

mkdir -p /app/servers
chmod 755 /app/servers

mkdir -p /var/log/supervisor
chmod 755 /var/log/supervisor

# Export APP_ENV and determine if dev mode
export APP_ENV="${APP_ENV:-}"
if [ -z "$APP_ENV" ] || [ "$APP_ENV" = "development" ]; then
    export FRONTEND_NUMPROCS=1
    echo -e "${GREEN}✓ Development mode enabled${NC}"
else
    export FRONTEND_NUMPROCS=0
    echo -e "${GREEN}✓ Production mode enabled${NC}"
fi

echo -e "${GREEN}✓ Directories prepared${NC}"

echo -e "${GREEN}Starting supervisord...${NC}"
exec /usr/bin/supervisord --nodaemon --configuration=/etc/supervisor/supervisord.conf --logfile=/dev/stdout --loglevel=info
