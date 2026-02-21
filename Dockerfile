FROM node:22-slim AS webapp-build
WORKDIR /webapp
COPY webapp/package.json webapp/pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY webapp/ .
RUN pnpm build

FROM python:3.12-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic/ alembic/
COPY src/ src/
COPY webapp/styles/ webapp/styles/
COPY --from=webapp-build /webapp/dist/ webapp/dist/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
