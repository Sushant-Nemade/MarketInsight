FROM node:24-alpine AS frontend
WORKDIR /site
COPY LICENSE NOTICE.md /
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build -- --logLevel error && node scripts/licenses.mjs

FROM python:3.13-slim AS runtime
WORKDIR /app
RUN python -m pip install --no-cache-dir uv==0.13.0
COPY pyproject.toml uv.lock LICENSE NOTICE.md README.md ./
COPY MarketInsight ./MarketInsight
COPY config ./config
COPY main.py ./
RUN uv sync --frozen --no-dev && useradd --system --uid 10001 market && mkdir -p /app/data && chown market:market /app/data
COPY --from=frontend /site/dist ./frontend/dist
USER market
ENV MARKET_DATABASE_PATH=/app/data/reports.sqlite
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]