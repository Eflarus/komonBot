# KomonBot — Telegram Web App + API + Ghost CMS

## Overview

Система управления мероприятиями и курсами для культурного пространства.
Архитектура: **FastAPI backend** + **Telegram Web App** (Mini App) + **Ghost CMS** интеграция.

Обычный Telegram-бот **не используется** — вся работа через Web App интерфейс.
Telegram используется только для: запуска Mini App, push-уведомлений, нотификаций о заявках.

**Деплой**: сервис работает на **конфигурируемом саброуте** основного Ghost-сайта
(например `https://komon.tot.pub/bot/`). Ghost и бэкенд живут за одним доменом,
Nginx проксирует саброут на FastAPI.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Package manager | uv |
| Web framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 (async, mapped_column) |
| Database | PostgreSQL 16 (asyncpg) |
| Migrations | Alembic |
| Telegram Bot API | aiogram 3.x (только webhook + Mini App launch) |
| Telegram Web App | Preact + HTM (no build step, CDN imports, ~3KB) |
| Ghost integration | Ghost Admin API (PyJWT + httpx) |
| Image storage | Ghost CMS (upload через Admin API) |
| Task scheduler | APScheduler (async) |
| Validation | Pydantic v2 |
| Rate limiting | slowapi (leaky bucket, per-IP) |
| Sanitization | bleach / markupsafe |
| Retry logic | tenacity (exponential backoff) |
| Logging | structlog (JSON, request_id) |
| Linting/Format | ruff, black |
| Testing | pytest + pytest-asyncio + httpx (AsyncClient) + respx (mock HTTP) |
| Containerization | Docker + docker-compose |

---

## Project Structure

```
komonBot/
├── bot.md                      # this file
├── pyproject.toml               # uv project, dependencies, ruff/black config
├── uv.lock
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory, lifespan
│   ├── config.py                # pydantic Settings (env vars)
│   ├── database.py              # async engine, sessionmaker, Base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py             # Event model
│   │   ├── course.py            # Course model
│   │   ├── user.py              # WhitelistUser model
│   │   ├── contact.py           # ContactMessage model
│   │   └── audit.py             # AuditLog model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── event.py             # Event Pydantic schemas
│   │   ├── course.py            # Course Pydantic schemas
│   │   ├── user.py              # User schemas
│   │   ├── contact.py           # Contact schemas
│   │   └── common.py            # Pagination, filters, etc.
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py              # Generic CRUD repository
│   │   ├── event.py             # EventRepository
│   │   ├── course.py            # CourseRepository
│   │   ├── user.py              # UserRepository
│   │   └── contact.py           # ContactRepository
│   ├── services/
│   │   ├── __init__.py
│   │   ├── event.py             # Event business logic + lifecycle
│   │   ├── course.py            # Course business logic + lifecycle
│   │   ├── ghost.py             # Ghost CMS client (upload images, update pages)
│   │   ├── content_page.py      # Ghost content page builder (events page, courses page)
│   │   ├── notification.py      # Telegram notification sender
│   │   ├── scheduler.py         # APScheduler tasks (reminders, auto-archive)
│   │   └── audit.py             # Audit logging service
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py            # main API router, includes sub-routers
│   │   ├── deps.py              # dependencies (get_db, get_current_user, verify_telegram)
│   │   ├── events.py            # /api/events CRUD endpoints
│   │   ├── courses.py           # /api/courses CRUD endpoints
│   │   ├── contacts.py          # /api/contacts — public submission + admin list
│   │   ├── users.py             # /api/users — whitelist management
│   │   └── webhook.py           # /webhook/telegram — aiogram webhook handler
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── setup.py             # Bot instance, dispatcher, webhook registration
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   └── start.py         # /start command — opens Web App
│   │   └── middlewares/
│   │       ├── __init__.py
│   │       └── auth.py          # whitelist check middleware
│   └── utils/
│       ├── __init__.py
│       ├── telegram_auth.py     # Telegram initData validation (HMAC)
│       └── ghost_jwt.py         # Ghost Admin API JWT token generation
├── entrypoint.sh                # alembic upgrade + uvicorn start
├── webapp/                       # Telegram Mini App frontend (Preact + HTM, no build)
│   ├── index.html               # SPA entry point (CDN imports)
│   ├── app.js                   # main app, hash router
│   ├── components/              # Preact components
│   │   ├── event-list.js
│   │   ├── event-form.js
│   │   ├── course-list.js
│   │   ├── course-form.js
│   │   ├── contact-list.js
│   │   └── user-list.js
│   ├── services/
│   │   └── api.js               # fetch wrapper with initData header + 401 handling
│   └── styles/
│       └── app.css              # Telegram theme vars (var(--tg-theme-bg-color) etc.)
└── tests/
    ├── __init__.py
    ├── conftest.py              # fixtures: async db, test client, mock ghost, etc.
    ├── factories.py             # model factories for tests
    ├── test_api/
    │   ├── __init__.py
    │   ├── test_events.py
    │   ├── test_courses.py
    │   ├── test_contacts.py
    │   └── test_users.py
    ├── test_services/
    │   ├── __init__.py
    │   ├── test_event_service.py
    │   ├── test_course_service.py
    │   ├── test_ghost_service.py
    │   ├── test_content_page.py
    │   └── test_notification.py
    └── test_models/
        ├── __init__.py
        └── test_models.py
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
    event_date: Mapped[date] = mapped_column(Date)                # YYYY-MM-DD
    event_time: Mapped[time] = mapped_column(Time)                # HH:MM
    cover_image: Mapped[str | None] = mapped_column(String(500))  # Ghost image URL (516x516)
    ticket_link: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus), default=EventStatus.DRAFT
    )
    order: Mapped[int] = mapped_column(default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger)    # TG user ID
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
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
    schedule: Mapped[str] = mapped_column(Text)                    # "Пн/Ср 19:00-20:30"
    image_desktop: Mapped[str | None] = mapped_column(String(500)) # Ghost URL, desktop card image
    image_mobile: Mapped[str | None] = mapped_column(String(500))  # Ghost URL, mobile card image
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[CourseStatus] = mapped_column(
        SQLEnum(CourseStatus), default=CourseStatus.DRAFT
    )
    order: Mapped[int] = mapped_column(default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
```

### WhitelistUser

```python
class WhitelistUser(Base):
    __tablename__ = "whitelist_users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    # YAGNI: no roles for now, all whitelisted users are admins
    added_by: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

### ContactMessage (заявки)

```python
class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))        # "event:5", "course:3", "site"
    is_processed: Mapped[bool] = mapped_column(default=False)
    processed_by: Mapped[int | None] = mapped_column(BigInteger)  # TG user ID
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column()
```

### AuditLog

```python
class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)   # TG user ID
    action: Mapped[str] = mapped_column(String(50))                 # "create", "update", "delete", "publish", ...
    entity_type: Mapped[str] = mapped_column(String(50))            # "event", "course", "user", ...
    entity_id: Mapped[int] = mapped_column()
    changes: Mapped[str | None] = mapped_column(Text)               # JSON diff {field: [old, new]}
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

---

## API Endpoints

### Authentication

Все admin-эндпоинты защищены через Telegram Web App `initData` validation.

```
Header: X-Telegram-Init-Data: <initData string>
```

Сервер валидирует HMAC подпись, извлекает `user.id`, проверяет whitelist.

### Events — `/api/events`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/events` | admin | Список событий (фильтр: `?status=draft&search=...`) |
| GET | `/api/events/{id}` | admin | Детали события |
| POST | `/api/events` | admin | Создать событие (status=draft) |
| PATCH | `/api/events/{id}` | admin | Обновить поля события |
| DELETE | `/api/events/{id}` | admin | Удалить событие (soft: status→archived, или hard) |
| POST | `/api/events/{id}/publish` | admin | Опубликовать → Ghost |
| POST | `/api/events/{id}/unpublish` | admin | Снять с публикации → Ghost draft |
| POST | `/api/events/{id}/cancel` | admin | Отменить → пометка "ОТМЕНЕНО" в Ghost |
| POST | `/api/events/{id}/upload-image` | admin | Загрузить обложку/фото |

### Courses — `/api/courses`

Полностью аналогично Events:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/courses` | admin | Список курсов |
| GET | `/api/courses/{id}` | admin | Детали курса |
| POST | `/api/courses` | admin | Создать курс |
| PATCH | `/api/courses/{id}` | admin | Обновить курс |
| DELETE | `/api/courses/{id}` | admin | Удалить курс |
| POST | `/api/courses/{id}/publish` | admin | Опубликовать → Ghost |
| POST | `/api/courses/{id}/unpublish` | admin | Снять с публикации |
| POST | `/api/courses/{id}/cancel` | admin | Отменить |
| POST | `/api/courses/{id}/upload-image` | admin | Загрузить изображение (`?type=desktop\|mobile`) |

### Contacts — `/api/contacts`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/contacts` | **public** | Отправить заявку (с сайта / Web App) |
| GET | `/api/contacts` | admin | Список заявок (`?is_processed=false`) |
| PATCH | `/api/contacts/{id}/process` | admin | Пометить заявку обработанной |

#### Security: `POST /api/contacts` (public endpoint)

Поскольку эндпоинт публичный, применяются следующие меры защиты:

| Мера | Реализация |
|------|-----------|
| **Rate limiting** | `slowapi` (leaky bucket) — **5 req/min per IP**, **20 req/hour per IP**. Возвращает `429 Too Many Requests` с `Retry-After` header |
| **Input validation** | Pydantic v2 schema с жёсткими ограничениями: `name` max 255 chars, `phone` regex `^\+?[\d\s\-\(\)]{7,20}$`, `message` max 2000 chars, `email` optional `EmailStr`, `source` enum/regex |
| **Input sanitization** | Все строковые поля: strip, collapse whitespace. `message` — strip HTML tags (`bleach.clean` или `markupsafe.escape`). Никакой raw HTML в БД |
| **SQL injection** | SQLAlchemy parameterized queries (ORM) — инъекция невозможна by design |
| **XSS** | Данные из `contact_messages` показываются только в TG-уведомлениях (plain text) и в admin Web App (React auto-escapes). В Ghost HTML карточки не используют данные из заявок |
| **CORS** | `CORSMiddleware` — whitelist только `GHOST_URL` + `WEBAPP_URL`. Без wildcard `*` |
| **Request size** | `max_content_length` — 16 KB для JSON body. Отсекает payload-бомбы |
| **Honeypot field** | Скрытое поле `website` (CSS `display:none`) в форме. Если заполнено → 201 OK но не сохраняем (silent drop для ботов) |

```python
# schemas/contact.py
class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(pattern=r"^\+?[\d\s\-\(\)]{7,20}$")
    email: EmailStr | None = None
    message: str = Field(min_length=1, max_length=2000)
    source: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=0)  # honeypot: must be empty

    @field_validator("name", "message")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        v = v.strip()
        v = re.sub(r"<[^>]+>", "", v)       # strip HTML tags
        v = re.sub(r"\s+", " ", v)          # collapse whitespace
        return v
```

### Users — `/api/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/users` | admin | Список пользователей whitelist |
| POST | `/api/users` | admin | Добавить пользователя |
| DELETE | `/api/users/{id}` | admin | Удалить из whitelist |

### Ghost Page Sync (internal, no public API)

Контент страниц "Афиша" и "Курсы" в Ghost **не подтягивается через JS fetch**.
Вместо этого при каждом изменении сущностей (create/update/delete/publish/unpublish/cancel)
бэкенд **пересобирает полный HTML** из актуальных опубликованных записей и
**перезаписывает контент** соответствующей Ghost-страницы через Admin API (`PUT /pages/{id}`).

Это означает:
- Нет публичного content API
- Нет JS на стороне Ghost — чистый статический HTML
- Страницы обновляются мгновенно при любом изменении через бот
- Нет зависимости от доступности backend в момент просмотра сайта

### Webhook — `/webhook/telegram`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/webhook/telegram` | Telegram IP | aiogram webhook handler |

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
1. Validate все обязательные поля заполнены (title, location, date, time; для курсов — description, schedule, cost)
2. `status = PUBLISHED`
3. Записать в audit log
4. **Пересобрать Ghost-страницу** (выборка всех PUBLISHED → build HTML → PUT page)
5. Отправить уведомление в TG: "Событие X опубликовано"

#### Unpublish flow:
1. `status = DRAFT`
2. Audit log + notification
3. **Пересобрать Ghost-страницу** (карточка исчезнет из выборки)

#### Cancel flow:
1. `status = CANCELLED`
2. Audit log + notification
3. **Пересобрать Ghost-страницу** (карточка исчезнет из выборки)

#### Auto-archive (scheduler):
1. Каждый день в 03:00 → найти PUBLISHED events с `event_date < today`
2. `status = ARCHIVED`
3. Audit log
4. **Пересобрать Ghost-страницу** (архивные карточки исчезнут)

### Contact submission flow:
1. `POST /api/contacts` — валидация + санитизация → сохранить в БД
2. Отправить Telegram-уведомление всем admin-пользователям:
   ```
   Новая заявка!
   Имя: {name}
   Телефон: {phone}
   Сообщение: {message}
   Источник: {source}
   ```
3. Вернуть `201 Created`

### Ghost page rebuild (triggered on every entity change):

При любом изменении опубликованных событий или курсов (create, update, delete,
publish, unpublish, cancel, auto-archive) система:

1. Делает выборку всех PUBLISHED записей, сортировка по `order`, затем по дате
2. Генерирует полный HTML из карточек (см. шаблоны ниже)
3. Вызывает Ghost Admin API: `PUT /pages/{page_id}` с новым `html`
4. Ghost-страница обновляется мгновенно — никакого JS на клиенте

#### HTML-шаблон карточки мероприятия (Ghost `kg-product-card`)

```html
<div class="kg-card kg-product-card">
    <div class="kg-product-card-container">
        <img src="{cover_image_url}" width="516" height="516"
             class="kg-product-card-image" loading="lazy">
        <div class="kg-product-card-title-container">
            <h4 class="kg-product-card-title">
                <span style="white-space: pre-wrap;">{title}</span>
            </h4>
        </div>
        <div class="kg-product-card-description">
            <p>
                <span style="white-space: pre-wrap;">{location}</span><br>
                <span style="white-space: pre-wrap;">{event_date_formatted}</span><br>
                <span style="white-space: pre-wrap;">{event_time}</span>
            </p>
        </div>
        <!-- ticket_link optional: render button only if present -->
        <a href="{ticket_link}" class="kg-product-card-button kg-product-card-btn-accent"
           target="_blank" rel="noopener noreferrer">
            <span>Купить билет</span>
        </a>
    </div>
</div>
```

#### HTML-шаблон карточки курса

```html
<div class="cource-card">
    <img class="smh" src="{image_desktop_url}" alt="{title}">
    <img class="pch" src="{image_mobile_url}" alt="{title}">
    <span class="price">{cost} {currency_symbol}</span>
    <div class="cource-desc">
        <h3 class="cource-header">{title}</h3>
        <p class="long-text smh">{description}</p>
        <details class="cource-more">
            <summary><button type="button">Узнать подробнее</button></summary>
            <h4>Даты</h4>
            <p>{schedule}</p>
            <!-- detailed_description optional -->
            <div><p>{detailed_description}</p></div>
        </details>
    </div>
</div>
```

> `<details>/<summary>` — нативный CSS-only toggle, не требует JS. Ghost 6.x не strip'ит эти теги.

Карточки курсов оборачиваются в контейнер:
```html
<div class="kg-width-wide col3">
    <!-- course cards here -->
</div>
```

#### Реализация (`services/content_page.py`)

```python
class ContentPageBuilder:
    """Builds HTML from published entities and pushes to Ghost pages."""

    def build_events_html(self, events: list[Event]) -> str:
        """Render all event cards into concatenated HTML string."""

    def build_courses_html(self, courses: list[Course]) -> str:
        """Render all course cards wrapped in container div."""

    def _render_event_card(self, event: Event) -> str:
        """Single event → kg-product-card HTML. Escape all user input."""

    def _render_course_card(self, course: Course) -> str:
        """Single course → cource-card HTML. Escape all user input."""

    async def sync_events_page(self) -> None:
        """Fetch PUBLISHED events → build HTML → PUT to Ghost page."""

    async def sync_courses_page(self) -> None:
        """Fetch PUBLISHED courses → build HTML → PUT to Ghost page."""
```

Вызывается из сервисов `EventService` / `CourseService` после каждой мутации:

```python
class EventService:
    async def publish(self, event_id: int, user_id: int) -> Event:
        # ... validate, update status ...
        await self.content_page_builder.sync_events_page()  # rebuild Ghost page

    async def update(self, event_id: int, data, user_id: int) -> Event:
        # ... update fields ...
        if event.status == EventStatus.PUBLISHED:
            await self.content_page_builder.sync_events_page()  # rebuild if was published
```

---

## Ghost CMS Integration

### Модель интеграции

Ghost используется **только как CMS для отображения** — весь контент генерируется
на стороне бэкенда и пушится в Ghost через Admin API.

Отдельные посты для событий/курсов **не создаются**. Вместо этого:
- Страница "Афиша" (`GHOST_EVENTS_PAGE_ID`) — содержит HTML-карточки всех актуальных мероприятий
- Страница "Курсы" (`GHOST_COURSES_PAGE_ID`) — содержит HTML-карточки всех актуальных курсов
- При каждом изменении → полный rebuild HTML → `PUT /pages/{id}` в Ghost

Изображения загружаются в Ghost через Admin API (`POST /images/upload`)
и хранятся в Ghost media storage. URL сохраняется в БД.

### Config

```env
GHOST_URL=https://your-ghost-site.com
GHOST_ADMIN_API_KEY=<id>:<secret>    # Admin API key (id:secret format)
GHOST_EVENTS_PAGE_ID=<page_id>       # Ghost page ID for "Афиша" page
GHOST_COURSES_PAGE_ID=<page_id>      # Ghost page ID for "Курсы" page
```

> `GHOST_CONTENT_API_KEY` не нужен — мы не читаем из Ghost, только пишем.

### Ghost Admin API Client (`services/ghost.py`)

```python
class GhostClient:
    """Async Ghost Admin API client using httpx."""

    async def upload_image(self, file_bytes: bytes, filename: str) -> str:
        """Upload image to Ghost via POST /images/upload, return public URL."""

    async def get_page(self, page_id: str) -> dict:
        """Get page by ID (needed for updated_at / ETag for concurrent updates)."""

    async def update_page_html(self, page_id: str, html: str) -> None:
        """Replace full HTML content of a Ghost page via PUT /pages/{id}."""

    def _make_jwt(self) -> str:
        """Generate short-lived JWT for Admin API auth (HS256, 5 min expiry)."""
```

### Ghost API flow (update page)

```
1. GET  /ghost/api/admin/pages/{page_id}/     → get current `updated_at`
2. PUT  /ghost/api/admin/pages/{page_id}/
   Body: { "pages": [{ "html": "<full rebuilt HTML>", "updated_at": "..." }] }
   Header: Authorization: Ghost {jwt}
```

> Ghost 6.x requires `updated_at` in PUT body to prevent concurrent edit conflicts.

---

## Telegram Bot Setup

### Минимальный бот (aiogram 3.x)

Бот нужен только для:
1. Команда `/start` — открывает Web App кнопкой
2. Отправка уведомлений (через `bot.send_message`)
3. Webhook endpoint для Telegram

```python
# bot/setup.py
from aiogram import Bot, Dispatcher
from aiogram.types import MenuButtonWebApp, WebAppInfo

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

async def setup_bot():
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Управление",
            web_app=WebAppInfo(url=settings.WEBAPP_URL)
        )
    )
    await bot.set_webhook(settings.WEBHOOK_URL)
```

### Notifications (`services/notification.py`)

```python
class NotificationService:
    async def notify_admins(self, message: str) -> None:
        """Send message to all whitelisted admin users."""

    async def notify_user(self, telegram_id: int, message: str) -> None:
        """Send message to specific user."""

    async def send_event_reminder(self, event: Event) -> None:
        """Send reminder about tomorrow's event to admins."""
```

---

## Telegram Web App (Mini App)

### Auth flow

1. User opens bot → clicks "Управление" (MenuButton) → opens Mini App
2. Mini App loads `Telegram.WebApp.initData` (signed by Telegram)
3. Every API request sends `X-Telegram-Init-Data` header
4. Backend validates HMAC, extracts `user.id`, checks whitelist

### Pages / Screens

```
┌─────────────────────────────────────┐
│         MAIN MENU                   │
│                                     │
│  [📅 Мероприятия]  [📚 Курсы]       │
│  [📩 Заявки]       [👥 Пользователи]│
│                                     │
└─────────────────────────────────────┘
         │
         ├── Events List (filter by status tabs)
         │     ├── Event Card → Event Detail / Edit
         │     └── [+ Создать] → Create Event Form
         │
         ├── Courses List (same pattern)
         │     ├── Course Card → Course Detail / Edit
         │     └── [+ Создать] → Create Course Form
         │
         ├── Contacts List (unprocessed first)
         │     └── Contact Card → Mark processed
         │
         └── Users List
               └── [+ Добавить] → Add user form
```

### Event Create / Edit Form

Поля формы:
- Название (text, required)
- Описание (textarea, required)
- Дата (date picker, required)
- Время (time picker, required)
- Место (text, required)
- Ссылка на билеты (url, optional)
- Обложка 516x516 (file upload, optional) — загружается в Ghost
- Порядок отображения (number, default 0)

Actions:
- Сохранить (draft)
- Опубликовать
- Отменить
- Удалить (с confirm dialog через `Telegram.WebApp.showConfirm`)

### Course Create / Edit Form

Поля:
- Название (text, required)
- Описание (textarea, required)
- Подробное описание (textarea, optional)
- Расписание (text, required)
- Стоимость (number, required)
- Валюта (select, default RUB)
- Изображение Desktop (file upload, optional) — для десктопной версии карточки
- Изображение Mobile (file upload, optional) — для мобильной версии карточки
- Порядок (number, default 0)

Actions: аналогично Events.

---

## Scheduler Tasks

```python
# services/scheduler.py — APScheduler jobs

async def auto_archive_events():
    """Run daily at 03:00. Archive published events with past dates."""

async def send_event_reminders():
    """Run daily at 10:00. Notify admins about tomorrow's events."""

```

---

## Configuration (`.env`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/komonbot

# App — subroute
ROOT_PATH=/bot                         # configurable subroute, used by FastAPI root_path
PUBLIC_URL=https://komon.tot.pub/bot   # full public base URL (for webhook registration, links)

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
WEBHOOK_SECRET=random-secret-string
# derived automatically:
#   WEBAPP_URL  = {PUBLIC_URL}/webapp
#   WEBHOOK_URL = {PUBLIC_URL}/webhook/telegram

# Ghost CMS
GHOST_URL=https://komon.tot.pub
GHOST_ADMIN_API_KEY=id:secret
GHOST_EVENTS_PAGE_ID=page-id
GHOST_COURSES_PAGE_ID=page-id

# App
SECRET_KEY=app-secret-for-signing
LOG_LEVEL=INFO
ADMIN_TELEGRAM_IDS=123456789,987654321   # initial admins (bootstrap)
ALLOWED_ORIGINS=https://komon.tot.pub    # CORS whitelist (same domain, but explicit)
```

---

## Docker

### `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic/ alembic/
COPY src/ src/
COPY webapp/ webapp/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
```

`entrypoint.sh`:
```bash
#!/bin/sh
set -e
uv run alembic upgrade head
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### `docker-compose.yml`

```yaml
services:
  app:
    build: .
    ports:
      - "127.0.0.1:8000:8000"    # only localhost, Nginx proxies
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./webapp:/app/webapp

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: komonbot
      POSTGRES_USER: komonbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U komonbot"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

---

## Reverse Proxy & Subroute

Сервис работает за Nginx на конфигурируемом саброуте Ghost-сайта.
FastAPI использует `root_path` для корректной генерации OpenAPI docs и ссылок.

### FastAPI root_path

```python
# src/main.py
from src.config import settings

app = FastAPI(
    title="KomonBot",
    root_path=settings.ROOT_PATH,    # e.g. "/bot"
)
```

Благодаря `root_path`:
- OpenAPI docs доступны на `https://komon.tot.pub/bot/docs`
- Все внутренние ссылки корректны
- Telegram webhook регистрируется как `{PUBLIC_URL}/webhook/telegram`

### URL structure (пример с `ROOT_PATH=/bot`)

```
https://komon.tot.pub/                  ← Ghost CMS (основной сайт)
https://komon.tot.pub/bot/api/events    ← FastAPI: events CRUD
https://komon.tot.pub/bot/api/courses   ← FastAPI: courses CRUD
https://komon.tot.pub/bot/api/contacts  ← FastAPI: contact form (public)
https://komon.tot.pub/bot/api/users     ← FastAPI: whitelist mgmt
https://komon.tot.pub/bot/webhook/telegram  ← Telegram webhook
https://komon.tot.pub/bot/webapp/       ← Telegram Mini App (static)
https://komon.tot.pub/bot/docs          ← OpenAPI Swagger UI
```

### Nginx config (добавить в существующий server block Ghost)

```nginx
# Inside existing Ghost server block for komon.tot.pub

# KomonBot backend API + webhook
location /bot/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket support (if needed for future features)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Image upload — allow larger body for cover uploads
    client_max_body_size 10M;
}
```

> **Важно**: `proxy_pass http://127.0.0.1:8000/` — trailing slash strip'ит `/bot/` prefix.
> FastAPI получает запросы без prefix, а `root_path` используется только для генерации URL'ов наружу.

### Config derivation (`src/config.py`)

```python
class Settings(BaseSettings):
    ROOT_PATH: str = "/bot"
    PUBLIC_URL: str = "https://komon.tot.pub/bot"

    # ... other settings ...

    @computed_field
    @property
    def WEBAPP_URL(self) -> str:
        return f"{self.PUBLIC_URL}/webapp"

    @computed_field
    @property
    def WEBHOOK_URL(self) -> str:
        return f"{self.PUBLIC_URL}/webhook/telegram"
```

---

## Testing Strategy

### Уровни тестов

1. **Unit tests** — models, schemas, utils (без БД)
2. **Integration tests** — repositories, services (с тестовой PostgreSQL)
3. **API tests** — endpoints через `httpx.AsyncClient` (с mock auth)
4. **Ghost mock tests** — services/ghost.py с `respx` или `httpx mock`

### Fixtures (`tests/conftest.py`)

```python
@pytest_asyncio.fixture
async def db_session():
    """Async test DB session with rollback after each test."""

@pytest.fixture
def client(db_session):
    """FastAPI test client with overridden deps."""

@pytest.fixture
def auth_headers():
    """Valid Telegram initData headers for test admin user."""

@pytest.fixture
def mock_ghost(respx_mock):
    """Mock Ghost Admin API responses."""
```

### Что тестируем

| Feature | Tests |
|---------|-------|
| Event CRUD API | create, read, list+filter, update, delete |
| Event lifecycle | publish, unpublish, cancel, auto-archive |
| Course CRUD API | same as events |
| Course lifecycle | same as events |
| Ghost sync | upload image, get page, update page HTML, error handling, retry |
| Content page builder | correct HTML output, event card template, course card template, ordering, filtering by status, empty state |
| Contact API | public submit, admin list, process, TG notification sent |
| Contact security | rate limiting (429 on excess), input validation (bad phone/email rejected), honeypot (silent drop), sanitization (HTML stripped), CORS |
| Auth | valid initData passes, invalid rejected, non-whitelisted rejected |
| Users API | add/remove whitelist, role checks |
| Audit log | actions recorded with correct user/entity/changes |
| Scheduler | auto-archive selects correct events, reminders sent |
| Telegram auth | HMAC validation, data extraction, expiry check |

### Run

```bash
uv run pytest tests/ -v --tb=short
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Implementation Order

### Phase 1 — Foundation
- [ ] Init project: `uv init`, pyproject.toml, dependencies
- [ ] Config (pydantic Settings + .env) — ROOT_PATH, PUBLIC_URL, computed WEBAPP_URL/WEBHOOK_URL
- [ ] Database setup (async engine, Base, session)
- [ ] Models (all 5 tables in SQLAlchemy 2.0 style)
- [ ] Alembic init + initial migration
- [ ] Pydantic schemas
- [ ] Base repository (generic async CRUD)
- [ ] Docker + docker-compose (app + postgres)
- [ ] FastAPI app factory with `root_path` from config
- [ ] Nginx subroute config (добавить location block в Ghost server)

### Phase 2 — API Core
- [ ] FastAPI app factory with lifespan
- [ ] Telegram initData auth dependency
- [ ] Events CRUD endpoints + repository + tests
- [ ] Courses CRUD endpoints + repository + tests
- [ ] Users (whitelist) endpoints + tests
- [ ] Audit log service + middleware

### Phase 3 — Ghost Integration
- [ ] Ghost JWT helper
- [ ] Ghost Admin API client (httpx) — upload_image, get_page, update_page_html
- [ ] ContentPageBuilder — event/course card HTML templates
- [ ] Event lifecycle → rebuild events Ghost page on every mutation
- [ ] Course lifecycle → rebuild courses Ghost page on every mutation
- [ ] Image upload to Ghost (event cover, course desktop/mobile)
- [ ] Tests with mocked Ghost API (respx)

### Phase 4 — Telegram & Notifications
- [ ] aiogram bot setup (webhook mode)
- [ ] `/start` command → Web App button
- [ ] Notification service (notify admins)
- [ ] Contact submission → TG notification + security (rate limit, validation, honeypot)
- [ ] Event reminder scheduler
- [ ] Auto-archive scheduler → triggers Ghost page rebuild

### Phase 5 — Web App (Mini App)
- [ ] Telegram Web App SDK integration
- [ ] Main menu screen
- [ ] Events list + create/edit/delete screens
- [ ] Courses list + create/edit/delete screens
- [ ] Contacts list + process screen
- [ ] Users list + add screen
- [ ] Image upload UI
- [ ] Status management UI (publish/unpublish/cancel buttons)

### Phase 6 — Polish
- [ ] ruff + black config in pyproject.toml
- [ ] CI pipeline (lint + test)
- [ ] Error handling & retry logic for Ghost API
- [ ] Rate limiting on public contact API
- [ ] Logging setup (structured JSON logs)
- [ ] .env.example + deployment docs

---

## Key Design Decisions

1. **Mapped column (SQLAlchemy 2.0)** вместо legacy `Column()` — type safety, IDE support
2. **BigInteger для telegram_id** — TG user IDs can exceed 32-bit int range
3. **Decimal для cost** вместо Float — точные финансовые значения
4. **Enum status в БД** — вместо boolean `active` — явный lifecycle
5. **Без ghost_post_id** — отдельные Ghost-посты не создаются, весь контент живёт в двух Ghost-страницах (afisha, courses), которые перезаписываются целиком
6. **Audit log** — отдельная таблица с JSON diff, не revision history
7. **Pre-generated HTML** — никакого JS fetch на Ghost-страницах; бэкенд пересобирает HTML и пушит через Admin API при каждом изменении сущностей. Страницы работают без зависимости от доступности бэкенда
8. **initData auth** — стандартный механизм Telegram Mini App, без custom tokens
9. **APScheduler** — легковесный, async-native, не нужен Celery/Redis для 3 простых задач
10. **Monorepo** — backend + webapp в одном репо для простоты деплоя
11. **Subroute deploy** — сервис за Nginx на конфигурируемом `ROOT_PATH`, FastAPI `root_path` для корректных URL. Ghost и бэкенд на одном домене — нет проблем с CORS/cookies

---

## Security Hardening

### S1. initData expiry validation

```python
# utils/telegram_auth.py
INIT_DATA_MAX_AGE = 600  # seconds (10 min)

def validate_init_data(init_data: str, bot_token: str) -> TelegramUser:
    """Validate Telegram WebApp initData."""
    parsed = parse_qs(init_data)

    # 1. Check auth_date freshness
    auth_date = int(parsed["auth_date"][0])
    if time.time() - auth_date > INIT_DATA_MAX_AGE:
        raise HTTPException(401, "initData expired")

    # 2. Verify HMAC-SHA256
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    check_string = "\n".join(f"{k}={v[0]}" for k, v in sorted(parsed.items()) if k != "hash")
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, parsed["hash"][0]):
        raise HTTPException(401, "Invalid initData signature")

    # 3. Extract user
    return TelegramUser.model_validate_json(parsed["user"][0])
```

### S2. Webhook secret verification

```python
# bot/setup.py
async def setup_bot():
    await bot.set_webhook(
        settings.WEBHOOK_URL,
        secret_token=settings.WEBHOOK_SECRET,  # Telegram sends this in header
    )

# api/webhook.py
@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(...),
):
    if not hmac.compare_digest(x_telegram_bot_api_secret_token, settings.WEBHOOK_SECRET):
        raise HTTPException(403, "Invalid webhook secret")
    # ... process update
```

### S3. Image upload validation

```python
# api/events.py, api/courses.py
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1 MB — Ghost page loads all images at once
MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",  # + check for WEBP at offset 8
}

async def validate_image(file: UploadFile) -> bytes:
    """Read, validate magic bytes + MIME, enforce size limit."""
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Image too large (max 1MB)")

    # Check magic bytes
    detected_type = None
    for magic, mime in MAGIC_BYTES.items():
        if content[:len(magic)] == magic:
            detected_type = mime
            break
    if detected_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Invalid image type. Allowed: JPEG, PNG, WebP")

    return content
```

> **SVG запрещён** — SVG может содержать inline JavaScript (XSS), a Ghost отдаёт его с `Content-Type: image/svg+xml`.

### S4. HTML escaping в ContentPageBuilder

```python
# services/content_page.py
from markupsafe import escape

class ContentPageBuilder:
    def _render_event_card(self, event: Event) -> str:
        """All user-supplied values MUST go through markupsafe.escape()."""
        title = escape(event.title)
        location = escape(event.location)
        # ... etc
        # ticket_link — дополнительно валидируется как URL (no javascript: scheme)
        if event.ticket_link:
            parsed = urlparse(event.ticket_link)
            if parsed.scheme not in ("http", "https"):
                ticket_link = None  # drop dangerous schemes
```

### S5. OpenAPI docs — disable in production

```python
# src/main.py
docs_url = "/docs" if settings.LOG_LEVEL == "DEBUG" else None
redoc_url = "/redoc" if settings.LOG_LEVEL == "DEBUG" else None

app = FastAPI(
    title="KomonBot",
    root_path=settings.ROOT_PATH,
    docs_url=docs_url,
    redoc_url=redoc_url,
)
```

### S6. Secrets management

```env
# .env — НЕ коммитить, добавить в .gitignore
# В production использовать Docker secrets или environment variables через systemd/Docker Swarm
```

```yaml
# docker-compose.yml — для production
services:
  app:
    environment:
      - DATABASE_URL            # pass via shell env, not .env file
      - GHOST_ADMIN_API_KEY
      - TELEGRAM_BOT_TOKEN
```

`.gitignore`:
```
.env
*.env
!.env.example
```

`.dockerignore`:
```
.env
.git
tests/
bot.md
*.md
```

---

## Resilience & Operations

### R1. Health check endpoint

```python
# api/router.py
@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Liveness + readiness probe."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        raise HTTPException(503, "Database unavailable")
```

```yaml
# docker-compose.yml — app service
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 10s
```

### R2. Ghost API retry + sync_pending

```python
# services/content_page.py
from tenacity import retry, stop_after_attempt, wait_exponential

class ContentPageBuilder:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _push_to_ghost(self, page_id: str, html: str) -> None:
        """PUT with retry. On final failure → log error, notify admins."""

    async def sync_events_page(self) -> None:
        try:
            html = self.build_events_html(events)
            await self._push_to_ghost(settings.GHOST_EVENTS_PAGE_ID, html)
        except Exception:
            logger.error("Ghost sync failed for events page after retries")
            await self.notification_service.notify_admins(
                "Ghost sync FAILED for events page. Manual check required."
            )
            # НЕ откатываем БД — данные в БД are source of truth.
            # Ghost page will be stale until next successful sync.
```

> **При следующем успешном изменении** страница обновится полностью (full rebuild), поэтому "stale" состояние самоисправляется.

### R3. PostgreSQL backups

```yaml
# docker-compose.yml — добавить сервис бэкапов
  db-backup:
    image: prodrigestivill/postgres-backup-local:16
    depends_on:
      - db
    environment:
      POSTGRES_HOST: db
      POSTGRES_DB: komonbot
      POSTGRES_USER: komonbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      SCHEDULE: "@daily"              # ежедневно
      BACKUP_KEEP_DAYS: 7
      BACKUP_KEEP_WEEKS: 4
      BACKUP_KEEP_MONTHS: 6
    volumes:
      - ./backups:/backups
```

Альтернатива — cron job на хосте:
```bash
# /etc/cron.d/komonbot-backup
0 4 * * * root docker exec komonbot-db-1 pg_dump -U komonbot komonbot | gzip > /backups/komonbot-$(date +\%Y\%m\%d).sql.gz
# retention: find /backups -name "*.sql.gz" -mtime +30 -delete
```

### R4. APScheduler — single instance guard

```python
# services/scheduler.py
# Гарантия: Uvicorn запускается с --workers 1 (default).
# Если в будущем нужно масштабировать — использовать advisory lock:

async def auto_archive_events():
    async with db_session() as session:
        # PostgreSQL advisory lock prevents duplicate execution
        result = await session.execute(text("SELECT pg_try_advisory_lock(1)"))
        if not result.scalar():
            return  # another worker already running this job
        try:
            # ... archive logic ...
        finally:
            await session.execute(text("SELECT pg_advisory_unlock(1)"))
```

В `docker-compose.yml` для uvicorn — явно 1 worker:
```yaml
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### R5. Timezone

```python
# config.py
TIMEZONE: str = "Europe/Moscow"

# services/scheduler.py
from zoneinfo import ZoneInfo

tz = ZoneInfo(settings.TIMEZONE)

scheduler.add_job(auto_archive_events, "cron", hour=3, minute=0, timezone=tz)
scheduler.add_job(send_event_reminders, "cron", hour=10, minute=0, timezone=tz)
```

```python
# В auto_archive:
today = datetime.now(tz).date()
# event_date < today — сравнение в локальном времени
```

### R6. Pagination

```python
# schemas/common.py
class PaginationParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)   # max 100 per request

# api/events.py
@router.get("/api/events")
async def list_events(
    pagination: PaginationParams = Depends(),
    status: EventStatus | None = None,
    search: str | None = Query(default=None, max_length=100),
):
    ...
```

### R7. Graceful shutdown

```python
# src/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await setup_bot()
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown(wait=True)     # wait for running jobs to finish
    await bot.session.close()         # close aiogram http session
    await engine.dispose()            # close DB connections
```

### R8. Admin seed on startup

```python
# src/main.py — inside lifespan startup
async def seed_initial_admins(session: AsyncSession):
    """Ensure ADMIN_TELEGRAM_IDS from env are in whitelist."""
    for tg_id in settings.ADMIN_TELEGRAM_IDS:
        existing = await session.execute(
            select(WhitelistUser).where(WhitelistUser.telegram_id == tg_id)
        )
        if not existing.scalar_one_or_none():
            session.add(WhitelistUser(
                telegram_id=tg_id, role="admin", added_by=None
            ))
    await session.commit()
```

### R9. Request ID + structured logging

```python
# src/main.py — middleware
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    # inject into logging context (structlog / contextvars)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

```python
# config logging
import structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
```

### R10. RBAC — editor vs admin

Упростить: убрать `role` из `WhitelistUser`. Все в whitelist — admin.
Если в будущем нужна гранулярность — добавить позже.

```python
# Сейчас: WhitelistUser.role удалить, все пользователи whitelist имеют полный доступ.
# Меньше кода, меньше багов, YAGNI.
```

---

## Engineering Decisions

### E1. Transaction boundary: DB commit vs Ghost sync

Проблема: `publish()` делает `status = PUBLISHED` в БД, потом `sync_events_page()`.
Если Ghost sync fail'ится — статус уже в БД, но на сайте ничего не изменилось.

Решение: **commit first, sync after** (current approach is correct).
- БД = source of truth. Ghost = read-only projection.
- Если Ghost упал → данные в БД корректны, Ghost обновится при следующей мутации.
- НЕ делать rollback при Ghost failure — это создаст inconsistency с audit log.
- Уведомление админу о failure достаточно (см. R2).

### E2. Ghost sync serialization (race condition)

Проблема: два быстрых PATCH подряд → два `sync_events_page()` запускаются параллельно →
оба читают одинаковый `updated_at` → первый PUT проходит → второй получает 409 Conflict.

Решение: `asyncio.Lock` на уровне `ContentPageBuilder`:

```python
class ContentPageBuilder:
    def __init__(self):
        self._events_lock = asyncio.Lock()
        self._courses_lock = asyncio.Lock()

    async def sync_events_page(self) -> None:
        async with self._events_lock:    # serialize Ghost writes
            events = await self.repo.get_published()
            html = self.build_events_html(events)
            await self._push_to_ghost(settings.GHOST_EVENTS_PAGE_ID, html)
```

При `--workers 1` этого достаточно. Lock гарантирует последовательный PUT.

### E3. initData expiry vs long form sessions

Проблема: `INIT_DATA_MAX_AGE = 600s` (10 мин). Админ открывает форму,
заполняет 15 минут, жмёт "Сохранить" → 401 Expired.

Решение: Web App при получении 401 вызывает `Telegram.WebApp.close()` +
`Telegram.WebApp.openTelegramLink()` для re-open. Либо:

```
Frontend: при 401 → показать toast "Сессия истекла" →
  Telegram.WebApp.close() → пользователь снова открывает Mini App.
  Draft данные сохранять в localStorage, восстанавливать при re-open.
```

### E4. `description` поле Event — назначение

`Event.description` не используется в Ghost HTML-карточке (там только title, location, date, time).
Поле используется **только в Web App** для админа — дополнительная информация при просмотре/редактировании.
Не выводится на сайт. Можно использовать как внутренние заметки.

### E5. Currency symbol mapping

`Course.currency` = `"RUB"` (ISO 4217), но в HTML шаблоне нужен символ `₽`.

```python
CURRENCY_SYMBOLS = {"RUB": "₽", "USD": "$", "EUR": "€"}

def currency_symbol(code: str) -> str:
    return CURRENCY_SYMBOLS.get(code, code)
```

### E6. "Узнать подробнее" — JS toggle на Ghost-странице

Кнопка "Узнать подробнее" в карточке курса раскрывает `detailed_description`.
Это требует **минимальный JS** на Ghost-странице (toggle visibility).

Вариант: CSS-only через `<details>/<summary>`:

```html
<details class="cource-more">
    <summary><button type="button">Узнать подробнее</button></summary>
    <h4>Даты</h4>
    <p>{schedule}</p>
    <div><p>{detailed_description}</p></div>
</details>
```

Преимущество: нет JS, работает нативно. Ghost не strip'ит `<details>`.

### E7. Alembic auto-migration on startup

```python
# src/main.py — lifespan startup, BEFORE app ready
from alembic.config import Config
from alembic import command

async def run_migrations():
    """Run pending Alembic migrations on startup."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

Или через Docker entrypoint:
```dockerfile
# Dockerfile
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
```

```bash
#!/bin/sh
# entrypoint.sh
set -e
uv run alembic upgrade head
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
```

> Entrypoint подход лучше — миграция отрабатывает до запуска приложения,
> нет race condition с healthcheck'ами.

### E8. API error response format

Стандартизировать формат ошибок для Web App:

```python
# schemas/common.py
class ErrorResponse(BaseModel):
    error: str           # machine-readable code: "validation_error", "not_found", "ghost_sync_failed"
    message: str         # human-readable (можно на русском для Web App)
    details: dict | None = None  # field-level errors for 422

# api/deps.py — exception handlers
@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.code, message=exc.message).model_dump()
    )
```

### E9. Upload-image response — return URL

```python
# api/events.py
@router.post("/api/events/{id}/upload-image", response_model=ImageUploadResponse)
async def upload_event_image(...):
    url = await ghost_client.upload_image(content, filename)
    event.cover_image = url
    await session.commit()
    return ImageUploadResponse(url=url)  # client needs this!

class ImageUploadResponse(BaseModel):
    url: str
```

### E10. DELETE semantics

Определить чётко:
- `DELETE /api/events/{id}` → **hard delete** (удаление из БД). Разрешено только для DRAFT.
- Для PUBLISHED/CANCELLED → сначала unpublish/archive, потом delete.
- ARCHIVED можно удалить hard.
- Триггерит Ghost page rebuild если сущность была PUBLISHED.

```python
async def delete(self, event_id: int, user_id: int) -> None:
    event = await self.repo.get(event_id)
    if event.status == EventStatus.PUBLISHED:
        raise AppError(400, "unpublish_first", "Сначала снимите с публикации")
    await self.repo.delete(event_id)
    # rebuild Ghost if it was published before (status transitions matter)
```

### E11. Web App tech stack: Preact + HTM

```
webapp/
├── index.html              # SPA entry point
├── app.js                  # main app, router
├── components/
│   ├── event-list.js
│   ├── event-form.js
│   ├── course-list.js
│   ├── course-form.js
│   ├── contact-list.js
│   ├── user-list.js
│   └── common/
│       ├── image-upload.js
│       └── status-badge.js
├── services/
│   ├── api.js              # fetch wrapper with initData header
│   └── auth.js             # Telegram.WebApp.initData extraction
└── styles/
    └── app.css             # Telegram WebApp theme variables
```

Без build step. CDN imports:
```html
<script type="module">
  import { h, render } from 'https://esm.sh/preact';
  import { useState } from 'https://esm.sh/preact/hooks';
  import htm from 'https://esm.sh/htm';
  const html = htm.bind(h);
</script>
```

FastAPI serves static:
```python
app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")
```

### E12. Dependency injection pattern

```python
# api/deps.py
async def get_ghost_client() -> GhostClient:
    return GhostClient(settings.GHOST_URL, settings.GHOST_ADMIN_API_KEY)

async def get_content_page_builder(
    session: AsyncSession = Depends(get_db),
    ghost: GhostClient = Depends(get_ghost_client),
    notification: NotificationService = Depends(get_notification_service),
) -> ContentPageBuilder:
    return ContentPageBuilder(
        event_repo=EventRepository(session),
        course_repo=CourseRepository(session),
        ghost=ghost,
        notification=notification,
    )

async def get_event_service(
    session: AsyncSession = Depends(get_db),
    builder: ContentPageBuilder = Depends(get_content_page_builder),
    audit: AuditService = Depends(get_audit_service),
) -> EventService:
    return EventService(
        repo=EventRepository(session),
        content_page_builder=builder,
        audit=audit,
    )
```

Это позволяет мокать любой слой в тестах через `app.dependency_overrides`.

### E13. Local development without Docker

```bash
# Quick start без Docker (нужен только PostgreSQL)
uv sync
cp .env.example .env                    # edit with local values
uv run alembic upgrade head
uv run uvicorn src.main:app --reload    # auto-reload on code changes
```

`.env.example` должен содержать все ключи с placeholder'ами.
`--reload` flag — только для dev (не в Dockerfile).

---

## Updated Implementation Checklist (additions)

### Phase 1 — Foundation (additions)
- [ ] `.gitignore` + `.dockerignore` (exclude `.env`, secrets)
- [ ] `TIMEZONE` config (Europe/Moscow)
- [ ] Health check endpoint (`GET /health`)
- [ ] Admin seed on startup from `ADMIN_TELEGRAM_IDS`
- [ ] `entrypoint.sh` (alembic upgrade head + uvicorn)
- [ ] `ErrorResponse` schema + global exception handlers
- [ ] Currency symbol mapping (RUB → ₽)

### Phase 2 — API Core (additions)
- [ ] Pagination (`offset`/`limit` with max=100) for all list endpoints
- [ ] initData expiry check (`auth_date` + MAX_AGE)
- [ ] Disable OpenAPI docs in production
- [ ] Request ID middleware + structured logging (structlog)
- [ ] Image upload validation (magic bytes, MIME, size limit, no SVG)
- [ ] Upload-image returns URL in response (`ImageUploadResponse`)
- [ ] DELETE — hard delete only for DRAFT/ARCHIVED, reject for PUBLISHED
- [ ] DI via `Depends()` — services get repos, ghost client, notification via injection

### Phase 3 — Ghost Integration (additions)
- [ ] `markupsafe.escape()` for all user input in HTML templates
- [ ] `ticket_link` scheme validation (only http/https)
- [ ] `tenacity` retry with exponential backoff for Ghost API
- [ ] Notification on Ghost sync failure
- [ ] Ghost `updated_at` conflict handling (409 → re-fetch + retry)
- [ ] `asyncio.Lock` per page in ContentPageBuilder (serialize concurrent syncs)
- [ ] Course card `<details>/<summary>` for "Узнать подробнее" (CSS-only, no JS)

### Phase 4 — Telegram & Notifications (additions)
- [ ] Webhook `secret_token` verification (X-Telegram-Bot-Api-Secret-Token)
- [ ] Uvicorn `--workers 1` (explicit, for APScheduler)
- [ ] Advisory lock guard for scheduler jobs
- [ ] Timezone-aware scheduler (Europe/Moscow)
- [ ] Graceful shutdown (scheduler, bot session, DB)

### Phase 5 — Web App (additions)
- [ ] Preact + HTM setup (CDN imports, no build step)
- [ ] `api.js` — fetch wrapper with initData header, 401 → re-open Mini App
- [ ] `localStorage` draft persistence (survive session re-open after 401)
- [ ] Telegram theme variables in CSS (`var(--tg-theme-bg-color)`)
- [ ] `app.mount("/webapp", StaticFiles(...))` in FastAPI

### Phase 6 — Polish (additions)
- [ ] PostgreSQL backup (docker service or cron)
- [ ] `.env.example` with all keys documented (no real values)
- [ ] Docker secrets for production deployment
- [ ] `pg_dump` restore procedure documented
- [ ] Local dev setup docs (uv sync, .env, uvicorn --reload)
