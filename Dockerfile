FROM python:3.10-slim

ENV APP_ENV=production

RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    nginx \
    curl \
    tmux \
    procps \
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


# Ensure mise has required tools
RUN mise use --global python@3.10
RUN mise use --global uv@latest
RUN pip install --user pipx
RUN mise use --global "pipx:fastmcp@latest"
RUN mise cache clean

# Update PATH so that MISE shims are available globally
ENV PATH="/root/.local/bin:/root/.local/share/mise/shims:$PATH"

# Copy built artifacts (build locally first with ./task prod docker build)
COPY backend/ /app/backend/
COPY frontend/dist/ /app/frontend/dist/

# Install backend dependencies only
# RUN cd /app/backend && mise exec uv@latest -- uv sync --frozen
RUN cd /app/backend && uv sync --frozen

COPY docker/ /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
