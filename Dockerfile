# Reflex + Railway single-container deployment
# Frontend (Next.js static) served by Caddy; backend (FastAPI/uvicorn) on port 8000
# Caddy proxies /_event/* and /ping to backend, serves everything else as static files
FROM python:3.12-slim

# Install Caddy (reverse proxy) and Node.js 20 (required by reflex export for Next.js build)
RUN apt-get update && apt-get install -y curl gnupg2 debian-keyring debian-archive-keyring \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update && apt-get install -y caddy nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build Next.js static frontend; output goes to .web/_static
RUN reflex export --frontend-only --no-zip \
    && mv .web/_static /srv

# Embed Caddyfile inline to avoid "not formatted" warning that causes WebSocket disconnects
# Routes: /_event/* and /ping -> backend at localhost:8000; everything else -> /srv static files
RUN printf ':%s {\n  encode gzip\n  @backend path /_event/* /ping /_upload/*\n  reverse_proxy @backend localhost:8000\n  root * /srv\n  file_server\n  try_files {path} /404.html\n}\n' "${PORT:-8080}" > /Caddyfile

EXPOSE 8080
# Start Reflex backend-only process and Caddy; PORT is injected by Railway at runtime
CMD ["sh", "-c", "reflex run --env prod --backend-only --backend-port 8000 & caddy run --config /Caddyfile --adapter caddyfile"]
