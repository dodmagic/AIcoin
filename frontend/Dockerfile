# syntax=docker/dockerfile:1

# Static frontend served by Nginx, which also reverse-proxies /api and /health
# to the backend container. Build context is the repository root.
FROM nginx:alpine

# Upgrade all packages to pick up latest security patches (e.g. CVE-2026-45447,
# CVE-2026-6732 affecting libcrypto3/libssl3/libxml2 in Alpine 3.23).
RUN apk upgrade --no-cache

# Reverse-proxy + static config.
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Static assets (live at the repository root).
COPY index.html /usr/share/nginx/html/index.html
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:80/ || exit 1
