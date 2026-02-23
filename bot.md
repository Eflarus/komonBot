# KomonBot — Telegram Web App + API + Ghost CMS

## Overview

Система управления мероприятиями и курсами для культурного пространства.
Архитектура: **FastAPI backend** + **Telegram Web App** (Mini App) + **Ghost CMS** интеграция.

Обычный Telegram-бот **не используется** — вся работа через Web App интерфейс.
Telegram используется только для: запуска Mini App, push-уведомлений, нотификаций о заявках, отправки бэкапов.

**Деплой**: сервис работает на **конфигурируемом саброуте** основного Ghost-сайта
(например `https://komon.tot.pub/bot/`). Ghost и бэкенд живут за одним доменом,
Nginx проксирует саброут на FastAPI.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Package manager | uv (backend), pnpm (webapp) |
| Web framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 (async, mapped_column) |
| Database | SQLite (aiosqlite, WAL mode) |
| Migrations | Alembic |
| Telegram Bot API | aiogram 3.x (webhook + Mini App launch only) |
| Telegram Web App | Preact + TypeScript + Vite (JSX/TSX, build step) |
| Ghost integration | Ghost Admin API (PyJWT + httpx) |
| Image storage | Ghost CMS (upload via Admin API) |
| Task scheduler | APScheduler (async) |
| Validation | Pydantic v2 |
| Rate limiting | slowapi (leaky bucket, per-IP) |
| Sanitization | bleach / markupsafe |
| Retry logic | tenacity (exponential backoff) |
| Logging | structlog (JSON, request_id) |
| Linting/Format | ruff, black |
| Testing | pytest + pytest-asyncio + httpx (AsyncClient) + respx (mock HTTP) |
| Containerization | Docker (multi-stage) + docker-compose |

---

## Project Structure

```
komonBot/
├── bot.md                      # this file — full system spec
├── pyproject.toml              # uv project, dependencies, ruff/black config
├── uv.lock
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── Dockerfile                  # multi-stage: Node.js (webapp build) + Python
├── docker-compose.yml
├── entrypoint.sh               # alembic upgrade + uvicorn start
├── .env.example
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory, lifespan, middleware
│   ├── config.py               # pydantic Settings (env vars)
│   ├── database.py             # async engine, sessionmaker, Base, SQLite WAL pragma
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py            # Event model + EventStatus enum
│   │   ├── course.py           # Course model + CourseStatus enum
│   │   ├── user.py             # WhitelistUser model
│   │   ├── contact.py          # ContactMessage model
│   │   └── audit.py            # AuditLog model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── event.py            # EventCreate, EventUpdate, EventResponse
│   │   ├── course.py           # CourseCreate, CourseUpdate, CourseResponse
│   │   ├── user.py             # UserCreate, UserResponse
│   │   ├── contact.py          # ContactCreate, ContactUpdate, ContactResponse
│   │   └── common.py           # PaginationParams, ErrorResponse, ImageUploadResponse
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py             # Generic CRUD repository
│   │   ├── event.py            # EventRepository
│   │   ├── course.py           # CourseRepository
│   │   ├── user.py             # UserRepository
│   │   └── contact.py          # ContactRepository
│   ├── services/
│   │   ├── __init__.py
│   │   ├── event.py            # Event business logic + lifecycle
│   │   ├── course.py           # Course business logic + lifecycle
│   │   ├── ghost.py            # Ghost CMS client (upload images, update pages)
│   │   ├── content_page.py     # Ghost content page builder (events page, courses page)
│   │   ├── notification.py     # Telegram notification sender
│   │   ├── scheduler.py        # APScheduler tasks (reminders, auto-archive, backup)
│   │   ├── backup.py           # SQLite backup with rotation + Telegram delivery
│   │   └── audit.py            # Audit logging service
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py           # main API router, includes sub-routers
│   │   ├── deps.py             # dependencies (get_db, get_current_user, verify_telegram)
│   │   ├── events.py           # /api/events CRUD endpoints
│   │   ├── courses.py          # /api/courses CRUD endpoints
│   │   ├── contacts.py         # /api/contacts — public submission + admin list
│   │   ├── users.py            # /api/users — whitelist management
│   │   └── webhook.py          # /webhook/telegram — aiogram webhook handler
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── setup.py            # Bot instance, dispatcher, webhook registration
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── start.py        # /start command — opens Web App
│   │   │   └── backup.py       # /backup command — sends fresh DB backup
│   │   └── middlewares/
│   │       ├── __init__.py
│   │       └── auth.py         # whitelist check middleware
│   └── utils/
│       ├── __init__.py
│       ├── telegram_auth.py    # Telegram initData validation (HMAC)
│       ├── ghost_jwt.py        # Ghost Admin API JWT token generation
│       └── image_validation.py # Magic byte + MIME + size validation
├── webapp/                      # Telegram Mini App frontend
│   ├── index.html              # SPA entry point (Vite)
│   ├── package.json            # preact, vite, typescript, @twa-dev/types
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json           # strict, jsxImportSource: "preact"
│   ├── vite.config.ts          # @preact/preset-vite, base: "/webapp/", proxy /api
│   ├── src/
│   │   ├── main.tsx            # App shell, hash router, Telegram BackButton
│   │   ├── types.ts            # Shared domain types (Event, Course, Contact, User)
│   │   ├── vite-env.d.ts       # Vite client types
│   │   ├── telegram.d.ts       # Telegram WebApp global type declaration
│   │   ├── services/
│   │   │   └── api.ts          # Typed fetch wrapper with initData header
│   │   └── components/
│   │       ├── Menu.tsx        # Main menu grid
│   │       ├── Toast.tsx       # Toast notification
│   │       ├── EventList.tsx   # Events list with status tabs + search
│   │       ├── EventForm.tsx   # Event create/edit with draft persistence
│   │       ├── CourseList.tsx  # Courses list with status tabs + search
│   │       ├── CourseForm.tsx  # Course create/edit with draft persistence
│   │       ├── ContactList.tsx # Contact requests list with processing
│   │       └── UserList.tsx    # User whitelist management
│   └── styles/
│       └── app.css             # Telegram theme vars (var(--tg-theme-bg-color) etc.)
└── tests/
    ├── __init__.py
    ├── conftest.py             # fixtures: async db, test client, mock ghost, etc.
    ├── factories.py            # model factories for tests
    ├── test_api/
    │   ├── __init__.py
    │   ├── test_events.py      # 14 tests
    │   ├── test_courses.py     # 11 tests
    │   ├── test_contacts.py    # 9 tests
    │   └── test_users.py       # 7 tests
    ├── test_services/
    │   ├── __init__.py
    │   └── test_content_page.py # 10 tests
    ├── test_models/
    │   ├── __init__.py
    │   └── test_models.py      # 4 tests
    └── test_utils/
        ├── __init__.py
        └── test_telegram_auth.py # 7 tests (HMAC, expiry, tamper, etc.)
```

---

## Data Models

### Event

```python
class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(255))
    event_date: Mapped[date] = mapped_column(Date)
    event_time: Mapped[time] = mapped_column(Time)
    cover_image: Mapped[str | None] = mapped_column(String(500))
    ticket_link: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus, native_enum=False, length=20), default=EventStatus.DRAFT
    )
    order: Mapped[int] = mapped_column(default=0)
    created_by: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.now
    )
```

### Course

```python
class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    detailed_description: Mapped[str | None] = mapped_column(Text)
    schedule: Mapped[str] = mapped_column(Text)
    image_desktop: Mapped[str | None] = mapped_column(String(500))
    image_mobile: Mapped[str | None] = mapped_column(String(500))
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[CourseStatus] = mapped_column(
        SQLEnum(CourseStatus, native_enum=False, length=20), default=CourseStatus.DRAFT
    )
    order: Mapped[int] = mapped_column(default=0)
    created_by: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.now
    )
```

### WhitelistUser

```python
class WhitelistUser(Base):
    __tablename__ = "whitelist_users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    added_by: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
```

### ContactMessage

```python
class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))
    is_processed: Mapped[bool] = mapped_column(default=False)
    processed_by: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    processed_at: Mapped[datetime | None] = mapped_column()
```

### AuditLog

```python
class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column()
    changes: Mapped[str | None] = mapped_column(Text)    # JSON diff
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
```

---

## API Endpoints

### Authentication

All admin endpoints are protected via Telegram Web App `initData` validation.

```
Header: X-Telegram-Init-Data: <initData string>
```

Server validates HMAC signature, extracts `user.id`, checks whitelist.
initData expires after 10 minutes (`INIT_DATA_MAX_AGE = 600`).

### Events — `/api/events`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/events` | admin | List events (`?status=draft&search=...&limit=50&offset=0`) |
| GET | `/api/events/{id}` | admin | Event details |
| POST | `/api/events` | admin | Create event (status=draft) |
| PATCH | `/api/events/{id}` | admin | Update event fields |
| DELETE | `/api/events/{id}` | admin | Delete event (only draft/archived) |
| POST | `/api/events/{id}/publish` | admin | Publish → Ghost page rebuild |
| POST | `/api/events/{id}/unpublish` | admin | Unpublish → Ghost page rebuild |
| POST | `/api/events/{id}/cancel` | admin | Cancel → Ghost page rebuild |
| POST | `/api/events/{id}/upload-image` | admin | Upload cover image to Ghost |

### Courses — `/api/courses`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/courses` | admin | List courses (same filters as events) |
| GET | `/api/courses/{id}` | admin | Course details |
| POST | `/api/courses` | admin | Create course |
| PATCH | `/api/courses/{id}` | admin | Update course |
| DELETE | `/api/courses/{id}` | admin | Delete course (only draft/archived) |
| POST | `/api/courses/{id}/publish` | admin | Publish → Ghost page rebuild |
| POST | `/api/courses/{id}/unpublish` | admin | Unpublish → Ghost page rebuild |
| POST | `/api/courses/{id}/cancel` | admin | Cancel → Ghost page rebuild |
| POST | `/api/courses/{id}/upload-image` | admin | Upload image (`?type=desktop\|mobile`) |

### Contacts — `/api/contacts`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/contacts` | **public** | Submit contact request (rate limited) |
| GET | `/api/contacts` | admin | List requests (`?is_processed=false`) |
| PATCH | `/api/contacts/{id}/process` | admin | Mark as processed |

#### Security: `POST /api/contacts` (public endpoint)

| Measure | Implementation |
|---------|---------------|
| **Rate limiting** | slowapi — 5 req/min, 20 req/hour per IP → 429 |
| **Input validation** | Pydantic: name max 255, phone regex, message max 2000, EmailStr |
| **Sanitization** | Strip HTML tags, collapse whitespace |
| **Honeypot** | Hidden `website` field — if filled → 201 but silently dropped |
| **CORS** | Whitelist only configured origins |
| **Request size** | 16 KB max body |

### Users — `/api/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/users` | admin | List whitelist users |
| POST | `/api/users` | admin | Add user (duplicate check) |
| DELETE | `/api/users/{id}` | admin | Remove user (cannot remove self) |

### Health — `/health`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | none | DB connectivity check |

### Webhook — `/webhook/telegram`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/webhook/telegram` | Telegram secret | aiogram webhook handler |

---

## Business Logic

### Event / Course Lifecycle

```
                ┌──────────┐
    create ───►│  DRAFT   │
                └────┬─────┘
                     │ publish
                     ▼
                ┌──────────┐
                │PUBLISHED │◄── unpublish returns to DRAFT
                └────┬─────┘
                     │
            ┌────────┼────────┐
            │ cancel          │ auto-archive (date passed)
            ▼                 ▼
       ┌──────────┐    ┌──────────┐
       │CANCELLED │    │ ARCHIVED │
       └──────────┘    └──────────┘
```

#### Publish flow:
1. Validate required fields (title, location, date, time; for courses — description, schedule, cost)
2. `status = PUBLISHED`
3. Record audit log
4. **Rebuild Ghost page** (fetch all PUBLISHED → build HTML → PUT page)
5. Notify admins via Telegram

#### Delete semantics:
- Hard delete (remove from DB). Allowed only for DRAFT/ARCHIVED.
- PUBLISHED entities must be unpublished first.
- Triggers Ghost page rebuild if entity was published.

### Contact submission flow:
1. `POST /api/contacts` — validate + sanitize → save to DB
2. Telegram notification to all admin users
3. Return `201 Created`

### Ghost page rebuild (triggered on every entity mutation):
1. Fetch all PUBLISHED records, sort by `order` then date
2. Generate HTML from card templates
3. `PUT /pages/{page_id}` via Ghost Admin API
4. Serialized with `asyncio.Lock` per page (prevent concurrent writes)
5. Retry with exponential backoff (tenacity, 3 attempts)
6. On final failure → notify admins, keep DB as source of truth

### Scheduler tasks:
- **auto_archive_events** — daily 03:00 (Europe/Moscow), archives past events
- **send_event_reminders** — daily 10:00, notifies admins about tomorrow's events
- **daily_backup** — daily 04:00, SQLite backup via `sqlite3.Connection.backup()` + rotation (keep last `BACKUP_KEEP`)
- **send_backup_telegram** — every 48 hours, sends backup file to `BACKUP_TELEGRAM_IDS` via Telegram

---

## Ghost CMS Integration

### Model

Ghost is used **only as a CMS for display** — all content is generated on the backend and pushed via Admin API.

Individual posts are **not created**. Instead:
- "Афиша" page (`GHOST_EVENTS_PAGE_ID`) — HTML cards of all published events
- "Курсы" page (`GHOST_COURSES_PAGE_ID`) — HTML cards of all published courses
- On each change → full HTML rebuild → `PUT /pages/{id}`

Images uploaded to Ghost via Admin API (`POST /images/upload`), URLs stored in DB.

### Ghost Admin API Client (`services/ghost.py`)

```python
class GhostClient:
    async def upload_image(self, file_bytes: bytes, filename: str) -> str
    async def get_page(self, page_id: str) -> dict
    async def update_page_html(self, page_id: str, html: str) -> None
```

JWT auth: HS256, 5 min expiry, `aud: "/admin/"`.

### HTML card templates

Event cards use Ghost `kg-product-card` structure. Course cards use `cource-card` with
`<details>/<summary>` for CSS-only "Узнать подробнее" toggle. All user-supplied values
escaped via `markupsafe.escape()`. `ticket_link` validated for http/https scheme only.

---

## Telegram Web App (Mini App)

### Architecture

- **Preact** — lightweight React-compatible UI library
- **TypeScript** — strict mode, shared domain types
- **Vite** — build tool with `@preact/preset-vite`, outputs to `webapp/dist/`
- **JSX/TSX** — type-checked props and autocompletion
- Hash-based routing (no external router library)
- Telegram WebApp SDK for BackButton, showConfirm, showAlert
- Type declarations via `@twa-dev/types`

### Build & dev

```bash
cd webapp
pnpm install        # install dependencies
pnpm dev            # Vite dev server (port 5173, proxies /api → localhost:8000)
pnpm build          # production build → webapp/dist/
pnpm typecheck      # tsc --noEmit
```

FastAPI serves `webapp/dist/` as static files at `/webapp/`.

### Auth flow

1. User opens bot → clicks "Управление" → opens Mini App
2. Mini App reads `Telegram.WebApp.initData`
3. Every API request sends `X-Telegram-Init-Data` header
4. Backend validates HMAC, checks whitelist
5. On 401 → toast "Сессия истекла" → `tg.close()`
6. Draft data persisted in `localStorage` to survive re-opens

### Screens

```
┌─────────────────────────────────────┐
│         MAIN MENU                   │
│                                     │
│  [📅 Мероприятия]  [📚 Курсы]       │
│  [📩 Заявки]       [👥 Пользователи]│
│                                     │
└─────────────────────────────────────┘
         │
         ├── Events List (status tabs, search)
         │     ├── Event Card → Edit form
         │     └── [+ Создать] → Create form (draft auto-saved)
         │
         ├── Courses List (same pattern)
         │     ├── Course Card → Edit form
         │     └── [+ Создать] → Create form (draft auto-saved)
         │
         ├── Contacts List (unprocessed/processed/all tabs)
         │     └── [Обработано] → mark processed
         │
         └── Users List
               └── [+ Добавить] → add user form (telegram_id, username, name)
```

### Typed API client (`src/services/api.ts`)

```typescript
export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, { body }),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, { body }),
  delete: <T>(path: string) => request<T>("DELETE", path),
  uploadFile<T>(path: string, file: File): Promise<T>,
};
```

### Domain types (`src/types.ts`)

```typescript
type EntityStatus = "draft" | "published" | "cancelled" | "archived";

interface Event { id, title, description, location, event_date, event_time, cover_image, ticket_link, status, order, ... }
interface Course { id, title, description, detailed_description, schedule, cost, currency, image_desktop, image_mobile, status, order, ... }
interface Contact { id, name, phone, email, message, source, is_processed, created_at, ... }
interface User { id, telegram_id, username, first_name, last_name, created_at }
interface PaginatedResponse<T> { items: T[], total: number }
```

---

## Configuration (`.env`)

```env
# Database (SQLite — file path relative to working directory)
DATABASE_URL=sqlite+aiosqlite:///data/komonbot.db

# App — subroute
ROOT_PATH=/bot
PUBLIC_URL=https://komon.tot.pub/bot

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
WEBHOOK_SECRET=random-secret-string

# Ghost CMS
GHOST_URL=https://komon.tot.pub
GHOST_ADMIN_API_KEY=id:secret
GHOST_EVENTS_PAGE_ID=page-id
GHOST_COURSES_PAGE_ID=page-id

# App
SECRET_KEY=app-secret-for-signing
LOG_LEVEL=INFO
TIMEZONE=Europe/Moscow
ADMIN_TELEGRAM_IDS_STR=123456789,987654321
ALLOWED_ORIGINS_STR=https://komon.tot.pub

# Backups
BACKUP_DIR=data/backups
BACKUP_KEEP=7
BACKUP_TELEGRAM_IDS_STR=123456789
```

Computed (derived automatically):
- `WEBAPP_URL = {PUBLIC_URL}/webapp`
- `WEBHOOK_URL = {PUBLIC_URL}/webhook/telegram`
- `ADMIN_TELEGRAM_IDS` — parsed from CSV
- `ALLOWED_ORIGINS` — parsed from CSV
- `BACKUP_TELEGRAM_IDS` — parsed from CSV

---

## Docker

### Dockerfile (multi-stage)

```dockerfile
# Stage 1: Build webapp
FROM node:22-slim AS webapp-build
WORKDIR /webapp
COPY webapp/package.json webapp/pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY webapp/ .
RUN pnpm build

# Stage 2: Python app
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY alembic.ini alembic/ src/ ./
COPY --from=webapp-build /webapp/dist/ webapp/dist/
COPY webapp/styles/ webapp/styles/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh
RUN mkdir -p /app/data
ENTRYPOINT ["./entrypoint.sh"]
```

### docker-compose.yml

```yaml
services:
  app:
    build: .
    ports:
      - "127.0.0.1:8000:8000"
    env_file: .env
    volumes:
      - dbdata:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

volumes:
  dbdata:
```

### entrypoint.sh

```bash
#!/bin/sh
set -e
uv run alembic upgrade head
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
```

---

## Reverse Proxy & Subroute

Service runs behind Nginx on a configurable subroute of the Ghost site.
FastAPI uses `root_path` for correct OpenAPI docs and URL generation.

### URL structure (example: `ROOT_PATH=/bot`)

```
https://komon.tot.pub/                  ← Ghost CMS (main site)
https://komon.tot.pub/bot/api/events    ← FastAPI: events CRUD
https://komon.tot.pub/bot/api/courses   ← FastAPI: courses CRUD
https://komon.tot.pub/bot/api/contacts  ← FastAPI: contact form (public)
https://komon.tot.pub/bot/api/users     ← FastAPI: whitelist mgmt
https://komon.tot.pub/bot/webhook/telegram  ← Telegram webhook
https://komon.tot.pub/bot/webapp/       ← Telegram Mini App (static)
https://komon.tot.pub/bot/docs          ← OpenAPI Swagger UI (DEBUG only)
```

### Nginx config

```nginx
location /bot/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    client_max_body_size 10M;
}
```

---

## Security

### S1. Telegram initData validation

HMAC-SHA256 signature check + `auth_date` freshness (10 min max).
Whitelist check against `whitelist_users` table.

### S2. Webhook secret verification

Telegram sends `X-Telegram-Bot-API-Secret-Token` header, compared via `hmac.compare_digest`.

### S3. Image upload validation

Magic byte detection (JPEG, PNG, WebP only), 1 MB size limit. SVG rejected (XSS vector).

### S4. HTML escaping in ContentPageBuilder

All user-supplied values go through `markupsafe.escape()`.
`ticket_link` validated for http/https scheme only.

### S5. OpenAPI docs — disabled in production

Swagger/ReDoc only available when `LOG_LEVEL=DEBUG`.

### S6. Secrets management

`.env` file gitignored. `.dockerignore` excludes `.env`, tests, docs.

---

## Testing

68 tests across all layers:

| Area | File | Tests |
|------|------|-------|
| Models | `test_models/test_models.py` | 4 (enum values) |
| Telegram auth | `test_utils/test_telegram_auth.py` | 7 (HMAC, expiry, tamper) |
| Events API | `test_api/test_events.py` | 14 (CRUD, lifecycle, auth) |
| Courses API | `test_api/test_courses.py` | 11 (CRUD, lifecycle) |
| Contacts API | `test_api/test_contacts.py` | 9 (submit, honeypot, validation, admin) |
| Users API | `test_api/test_users.py` | 7 (list, add, delete, self-removal) |
| Content page | `test_services/test_content_page.py` | 10 (HTML output, XSS escaping) |
| Backup | `test_services/test_backup.py` | 10 (create, rotate, send, errors) |

```bash
uv run pytest tests/ -v
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Key Design Decisions

1. **SQLAlchemy 2.0 mapped_column** — type safety, IDE support
2. **SQLite** — zero-config embedded DB, WAL mode for concurrent reads, no external service needed
3. **Decimal for cost** — accurate financial values
4. **Enum as VARCHAR** — `native_enum=False` for SQLite compatibility, stored as `String(20)`
5. **No ghost_post_id** — content lives in two Ghost pages, rebuilt entirely on each change
6. **Audit log** — separate table with JSON diff, not revision history
7. **Pre-generated HTML** — no JS on Ghost pages; backend rebuilds and pushes HTML
8. **initData auth** — standard Telegram Mini App mechanism
9. **APScheduler** — lightweight async, no need for Celery/Redis
10. **Monorepo** — backend + webapp in one repo for simple deployment
11. **Subroute deploy** — configurable `ROOT_PATH`, Ghost and backend on same domain
12. **Vite + TypeScript** — type-checked webapp with build step, JSX autocompletion
13. **Preact** — ~3KB React-compatible, minimal bundle size for Telegram Mini App
14. **asyncio.Lock for Ghost sync** — serializes concurrent page writes (single worker)
15. **DB = source of truth** — Ghost failures don't rollback DB; self-heals on next mutation
