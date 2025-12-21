FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    build-essential \
    supervisor \
    nginx \
    nodejs \
    npm \
    parallel \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Install Mise early
RUN curl -L https://mise.jdx.dev/install.sh -o /tmp/mise-install.sh && sh /tmp/mise-install.sh

RUN ln -s /root/.local/bin/mise /usr/local/bin/mise

ENV PATH="/root/.local/bin:$PATH" \
    MISE_ACTIVATE_DIR=1

# Install Overmind
COPY docker/overmind-v2.5.1-linux-amd64.gz /tmp/overmind.gz
RUN gunzip /tmp/overmind.gz \
    && mv /tmp/overmind /usr/local/bin/overmind \
    && chmod +x /usr/local/bin/overmind

ENV APP_ENV=production
WORKDIR /app

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Install uv globally
RUN pip install uv && uv pip install --system fastmcp

# RUN parallel ::: "cd /app/backend && uv sync --frozen" "cd /app/frontend && npm install && npm run build"

COPY docker/ /
RUN chmod +x /entrypoint.sh

EXPOSE 8000 8100-8199

ENTRYPOINT ["/entrypoint.sh"]
