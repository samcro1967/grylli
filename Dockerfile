# ---------- Build stage ----------
FROM python:3.12-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRYLLI_MODE=prod

WORKDIR /grylli

# System build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc nodejs npm gettext \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Node deps and frontend build
COPY package*.json ./
COPY scripts/generate_versions.js ./scripts/generate_versions.js
RUN npm ci

# Generate version.json with frontend versions
RUN mkdir -p /grylli/app/static
RUN node ./scripts/generate_versions.js

COPY . .

RUN npm run build

# ---------- Runtime stage ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRYLLI_MODE=prod

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget bash nano iputils-ping dnsutils jq \
 && rm -rf /var/lib/apt/lists/*

ARG PUID=1000
ARG PGID=1000

RUN groupadd -g ${PGID} grylli && \
    useradd -u ${PUID} -g ${PGID} -m -s /bin/bash grylli

WORKDIR /grylli

# Copy local config/entrypoint files and requirements in one layer
COPY gunicorn.conf.py wsgi.py requirements.txt ./

# Install only runtime Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy built application code and assets from the build stage
COPY --from=build /grylli/app /grylli/app

# Copy tools directly from context (not from build stage)
COPY tools /grylli/tools

RUN chown -R grylli:grylli /grylli

USER grylli

LABEL org.opencontainers.image.source="https://github.com/samcro1967/grylli"

CMD ["gunicorn", "-c", "gunicorn.conf.py", "-b", "0.0.0.0:5069", "wsgi:app"]
