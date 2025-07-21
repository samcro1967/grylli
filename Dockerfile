# ---------- Go Build Stage ----------
FROM golang:1.24.4-bookworm AS go-builder
WORKDIR /app

# Copy both Go source files
COPY healthcheck.go .
COPY entrypoint.go .

# Build both binaries
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o healthcheck ./healthcheck.go && \
    CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o entrypoint ./entrypoint.go

# ---------- Build Stage ----------
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRYLLI_MODE=prod

WORKDIR /grylli

# Install system dependencies (without Puppeteer-related packages)
RUN apt-get update && apt-get install -y \
    build-essential gcc nodejs npm gettext \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

# Copy pre-built assets (generated locally in app/static/)
COPY ./app/templates/static/css/critical.css /grylli/app/templates/static/css/critical.css
COPY ./app/static/version.json /grylli/app/static/version.json
COPY ./app/static/daisyui-themes.json /grylli/app/static/daisyui-themes.json


# Copy the source files (excluding any build steps)
COPY . .

# ---------- Final Runtime Stage ----------
FROM gcr.io/distroless/python3-debian12

ENV GRYLLI_MODE=prod
WORKDIR /grylli

# Copy the app and pre-built assets to the runtime image
COPY --from=build /grylli/app /grylli/app
COPY --from=build /grylli/migrations /grylli/migrations
COPY --from=build /grylli/wsgi.py /grylli/wsgi.py
COPY --from=build /grylli/gunicorn.conf.py /grylli/gunicorn.conf.py
COPY --from=build /grylli/tools /grylli/tools
COPY --from=build /grylli/verify_file_integrity.py /grylli/verify_file_integrity.py
COPY --from=build /grylli/file_hashes.sha256 /grylli/file_hashes.sha256

# This includes all installed Python packages (like gunicorn)
COPY --from=build /usr/local /usr/local

# Copy healthcheck and entrypoint binaries
COPY --from=go-builder /app/healthcheck /healthcheck
COPY --from=go-builder /app/entrypoint /entrypoint

# Match Python version exactly
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages"

# Gunicorn will now work
ENTRYPOINT ["/entrypoint"]
