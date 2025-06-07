# ---------- Go Build Stage ----------
FROM golang:1.24.4-bookworm AS go-builder
WORKDIR /app

# Copy both Go source files
COPY healthcheck.go .
COPY entrypoint.go .

# Build both binaries
RUN CGO_ENABLED=0 GOOS=linux go build -o healthcheck ./healthcheck.go && \
    CGO_ENABLED=0 GOOS=linux go build -o entrypoint ./entrypoint.go

# ---------- Build Stage ----------
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRYLLI_MODE=prod

WORKDIR /grylli

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc nodejs npm gettext \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps into system path (/usr/local/)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Frontend build
COPY package*.json ./ 
COPY scripts/generate_versions.js ./scripts/generate_versions.js
RUN npm ci && mkdir -p /grylli/app/static && node ./scripts/generate_versions.js

# Copy full source
COPY . .

# Compile and strip Python source
RUN python -m compileall -b /grylli/app && \
    find /grylli/app -name "*.py" ! -name "config.py" ! -name "wsgi.py" -type f -delete

# ---------- Final Runtime Stage ----------
FROM gcr.io/distroless/python3-debian12

ENV GRYLLI_MODE=prod
WORKDIR /grylli

# Copy the app to the runtime image
COPY --from=build /grylli/app /grylli/app
COPY --from=build /grylli/migrations /grylli/migrations
COPY --from=build /grylli/wsgi.py /grylli/wsgi.py
COPY --from=build /grylli/gunicorn.conf.py /grylli/gunicorn.conf.py
COPY --from=build /grylli/tools /grylli/tools

# This includes all installed Python packages (like gunicorn)
COPY --from=build /usr/local /usr/local

# Copy healthcheck and entrypoint binaries
COPY --from=go-builder /app/healthcheck /healthcheck
COPY --from=go-builder /app/entrypoint /entrypoint

# Match Python version exactly
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages"

# Gunicorn will now work
ENTRYPOINT ["/entrypoint"]
