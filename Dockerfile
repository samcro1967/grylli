# ---------- Go Build Stage ----------
FROM golang:1.24.6-bookworm AS go-builder
WORKDIR /app

# Copy both Go source files
COPY healthcheck.go .
COPY entrypoint.go .

# Build both binaries
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o healthcheck ./healthcheck.go && \
    CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o entrypoint ./entrypoint.go

RUN strip healthcheck entrypoint

# ---------- Build Stage ----------
FROM python:3.12-slim-bookworm AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRYLLI_MODE=prod

WORKDIR /grylli

# Install only minimal system deps (no compilers needed anymore)
RUN apt-get update && apt-get install -y \
    nodejs npm \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*
#gettext

# Copy requirements and prebuilt wheels
COPY requirements.txt ./
COPY wheelhouse /wheelhouse

# Install deps from prebuilt wheels only
RUN pip install --find-links=/wheelhouse --requirement requirements.txt

# Copy pre-built assets
COPY ./app/static /grylli/app/static
#COPY ./app/static/css/critical.css /grylli/app/static/css/critical.css
#COPY ./app/static/version.json /grylli/app/static/version.json
#COPY ./app/static/daisyui-themes.json /grylli/app/static/daisyui-themes.json
COPY ./app/assets/fonts /grylli/app/assets/fonts

# Copy the full source tree (app, scripts, config, etc.)
COPY . .

# ✅ Compile all .py files to .pyc beside them
RUN python -m compileall -b -f app

# ✅ Delete all .py files (except config.py if needed)
RUN find app -type f -name '*.py' ! -name 'config.py' -delete

# ✅ Generate hash manifest using only .pyc/.html/.jf
ENV GRYLLI_COMPILE_ONLY=1
RUN python3 generate_hashes.py

# Clean up runtime-imported cache again
RUN find app -type d -name '__pycache__' -exec rm -rf {} +

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
#COPY ./app/assets/fonts /grylli/app/assets/fonts
COPY --from=build /grylli/scripts/generate_fonts_css.py /grylli/scripts/generate_fonts_css.py

# This includes all installed Python packages (like gunicorn)
COPY --from=build /usr/local /usr/local

# Copy healthcheck and entrypoint binaries
COPY --from=go-builder /app/healthcheck /healthcheck
COPY --from=go-builder /app/entrypoint /entrypoint

# Match Python version exactly
ENV PYTHONPATH="/usr/local/lib/python3.11/site-packages"

# Gunicorn will now work
ENTRYPOINT ["/entrypoint"]
