# KomonBot

Telegram Web App + FastAPI backend + Ghost CMS integration for managing events and courses at a cultural space.

## Architecture

- **Backend**: FastAPI (async) with SQLAlchemy 2.0, SQLite (WAL mode), Alembic migrations
- **Frontend**: Preact + TypeScript Mini App (Vite build), served as static files
- **Bot**: aiogram 3.x — webhook only, launches the Mini App
- **CMS**: Ghost Admin API — backend pushes pre-rendered HTML to Ghost pages
- **Scheduling**: APScheduler — auto-archive past events, daily reminders

All admin operations happen through the Telegram Mini App. The bot itself only handles `/start`.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22+ with pnpm

### Local Development

```bash
# Clone and setup
git clone <repo-url> && cd komonBot
cp .env.example .env        # edit with your values

# Backend
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --reload --port 8000

# Webapp (separate terminal)
cd webapp
pnpm install
pnpm dev                     # Vite dev server on :5173, proxies /api → :8000
```

### Docker

```bash
cp .env.example .env         # edit with your values
docker compose up --build
```

The app will be available at `http://localhost:8000`. Webapp at `http://localhost:8000/webapp/`.

## Configuration

All configuration via environment variables (`.env` file):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLite connection string (`sqlite+aiosqlite:///data/komonbot.db`) |
| `ROOT_PATH` | Subroute prefix (e.g., `/bot`) |
| `PUBLIC_URL` | Full public base URL (e.g., `https://komon.tot.pub/bot`) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `WEBHOOK_SECRET` | Secret for Telegram webhook verification |
| `GHOST_URL` | Ghost CMS base URL |
| `GHOST_ADMIN_API_KEY` | Ghost Admin API key (`id:secret` format) |
| `GHOST_EVENTS_PAGE_ID` | Ghost page ID for events |
| `GHOST_COURSES_PAGE_ID` | Ghost page ID for courses |
| `SECRET_KEY` | App secret for signing |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` |
| `TIMEZONE` | Timezone for scheduler (default: `Europe/Moscow`) |
| `ADMIN_TELEGRAM_IDS_STR` | Comma-separated initial admin Telegram IDs |
| `ALLOWED_ORIGINS_STR` | Comma-separated CORS origins |

## API

All admin endpoints require Telegram `initData` in `X-Telegram-Init-Data` header.

| Endpoint | Description |
|----------|-------------|
| `GET /api/events` | List events (filter by status, search) |
| `POST /api/events` | Create event |
| `PATCH /api/events/{id}` | Update event |
| `DELETE /api/events/{id}` | Delete event (draft/archived only) |
| `POST /api/events/{id}/publish` | Publish → Ghost sync |
| `POST /api/events/{id}/upload-image` | Upload cover image |
| `GET /api/courses` | List courses |
| `POST /api/courses` | Create course |
| `POST /api/contacts` | Submit contact request (**public**, rate-limited) |
| `GET /api/contacts` | List contact requests |
| `GET /api/users` | List whitelisted users |
| `POST /api/users` | Add user to whitelist |
| `GET /health` | Health check |

Full API docs available at `/docs` when `LOG_LEVEL=DEBUG`.

## Webapp

The Mini App is a Preact + TypeScript SPA built with Vite:

```bash
cd webapp
pnpm install          # install dependencies
pnpm dev              # dev server with HMR
pnpm build            # production build → dist/
pnpm typecheck        # type check without emitting
```

Screens: Main menu → Events (list/create/edit) → Courses (list/create/edit) → Contacts (list/process) → Users (list/add).

## Testing

```bash
uv run pytest tests/ -v                              # run all 58 tests
uv run pytest tests/ -v --cov=src --cov-report=term  # with coverage
```

## Deployment

The service is designed to run behind Nginx on a subroute of a Ghost site:

```nginx
location /bot/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 10M;
}
```

## Project Documentation

See [bot.md](bot.md) for the full system specification: data models, business logic, Ghost integration details, security measures, and design decisions.
