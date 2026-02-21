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
| Telegram Web App | React/Preact или Vanilla JS (через Telegram Web App SDK) |
| Ghost integration | Ghost Admin API (PyJWT + httpx) |
| Image storage | Ghost CMS (upload через Admin API) |
| Task scheduler | APScheduler (async) |
| Validation | Pydantic v2 |
| Rate limiting | slowapi (leaky bucket, per-IP) |
| Sanitization | bleach / markupsafe |
| Linting/Format | ruff, black |
| Testing | pytest + pytest-asyncio + httpx (AsyncClient) |
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
├── webapp/                       # Telegram Mini App frontend
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── ...
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
    currency: Mapped[str] = mapped_column(String(3), default="ILS")
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
    role: Mapped[str] = mapped_column(String(20), default="editor")  # "admin" | "editor"
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
        <div class="cource-more">
            <h4>Даты</h4>
            <p>{schedule}</p>
            <!-- detailed_description optional -->
            <div><p>{detailed_description}</p></div>
        </div>
        <button>Узнать подробнее</button>
    </div>
</div>
```

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
- Валюта (select, default ILS)
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

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
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
