# Changelog

## [2026-02-28] Security Hardening — Round 2

Follow-up fixes after hard-critic review (5.5/10 → 8/10).

- **Body size middleware rewritten as ASGI middleware** — Previous `@app.middleware("http")` approach only checked `Content-Length` header (easily omitted/spoofed). New `BodySizeLimitMiddleware` wraps the ASGI `receive` callable to count actual bytes streamed. Handles malformed `Content-Length` without crashing. Tracks whether response headers were already sent to avoid ASGI double-response violation. (`src/main.py`)

- **Webhook secret empty string bypass** — `hmac.compare_digest("", "")` returned `True` when `WEBHOOK_SECRET` was not configured. Now rejects with 403 when secret is empty. (`src/api/webhook.py`)

- **RBAC enforced on event/course deletion** — Delete endpoints now require `get_admin_user` (admin role). Editors can still create, edit, and manage lifecycle. (`src/api/events.py`, `src/api/courses.py`)

- **Notification throttle race condition** — Added `asyncio.Lock` to `notify_contact_submission()` to prevent concurrent requests from bypassing the 30s throttle window. (`src/services/notification.py`)

- **Notifications restricted to admins** — `notify_admins()` now queries `get_admin_telegram_ids()` instead of `get_all_telegram_ids()`, so editors don't receive admin notifications. Uses `ROLE_ADMIN` constant. (`src/services/notification.py`, `src/repositories/user.py`)

- **Timing check upper bound** — Stale `form_ts` (>1 hour old) now silently dropped. Previously only checked for too-fast submissions. (`src/api/contacts.py`, `src/schemas/contact.py`)

- **CORS methods/headers restricted** — Replaced `allow_methods=["*"]` / `allow_headers=["*"]` with explicit lists. (`src/main.py`)

- **Silent notification failure logged** — `except Exception: pass` replaced with `logger.exception()`. (`src/api/contacts.py`)

### Test Coverage

- `test_timing_check.py` — Added stale timestamp test (4 total)
- `test_body_size.py` — Added no-Content-Length body rejection test (4 total)
- `test_api/test_events.py` — Added RBAC tests: editor create/delete, admin delete (3 new)
- `test_api/test_courses.py` — Added RBAC tests: editor create/delete, admin delete (3 new)

Total: **110 tests passing**.

---

## [2026-02-28] Security Audit & Hardening

Comprehensive security audit identified 10 vulnerabilities across the API, bot handlers, and infrastructure. All issues fixed and tested.

### CRITICAL

- **Rate limit bypass behind proxy** — `slowapi` used raw `remote_address` (always `127.0.0.1` behind nginx). Now extracts real client IP from `X-Forwarded-For` / `X-Real-IP` headers. (`src/api/contacts.py`)

### HIGH

- **Notification flood via contact spam** — Each contact submission sent a Telegram message to all admins. An attacker could send 5 requests/minute = 300 messages/hour. Added throttle: max 1 contact notification per 30 seconds, with suppressed count in next message. (`src/services/notification.py`)

- **CORS wildcard fallback** — When `ALLOWED_ORIGINS` was not configured, CORS allowed all origins (`["*"]`). Now CORS middleware is not added at all when unconfigured (same-origin only). (`src/main.py`)

- **No role separation** — All whitelisted users had identical permissions. Any user could add/remove other users, including revoking the original admin. Added `role` column (`admin`/`editor`). Only admins can manage the whitelist. Editors retain full access to events, courses, contacts. (`src/models/user.py`, `src/api/deps.py`, `src/api/users.py`, migration)

- **Unsanitized image filenames** — User-provided filenames were passed directly to Ghost and used in URL paths (`/uploads/{filename}`). Path traversal and stored XSS possible. Now generates UUID-based filenames with correct extension from detected MIME type. (`src/utils/image_validation.py`, `src/api/events.py`, `src/api/courses.py`)

### MEDIUM

- **Honeypot trivially bypassed** — Added server-side timing check: submissions with `form_ts` arriving faster than 3 seconds are silently dropped. Bots that submit instantly are caught even if they skip the honeypot. (`src/api/contacts.py`, `src/schemas/contact.py`)

- **initData replay window too long** — Reduced from 10 minutes to 5 minutes. (`src/utils/telegram_auth.py`)

- **Verbose error messages** — Auth errors revealed specific failure reasons (`"initData expired"`, `"Invalid signature"`), letting attackers distinguish attack scenarios. All auth errors now return `"Authentication failed"`. `NotFoundError` returns `"Resource not found"` instead of entity name and ID. (`src/utils/telegram_auth.py`, `src/exceptions.py`)

- **No request body size limit** — No global limit on request body size. An attacker could send 100MB+ payloads to exhaust server memory. Added 2MB ASGI-level body size limit with stream counting. (`src/main.py`)

### LOW

- **Default SECRET_KEY** — `SECRET_KEY` defaulted to `"change-me"`. Removed default (now empty string). Startup logs warnings if `SECRET_KEY` or `WEBHOOK_SECRET` are not configured. (`src/config.py`, `src/main.py`)

### Test Coverage

Added 36 new tests:
- `test_security/test_rate_limit.py` — IP extraction from proxy headers (6 tests)
- `test_security/test_notification_throttle.py` — Notification throttling (3 tests)
- `test_security/test_filename_sanitize.py` — UUID filename generation (6 tests)
- `test_security/test_timing_check.py` — Anti-bot timing validation (4 tests)
- `test_security/test_body_size.py` — Request size limit (4 tests)
- `test_api/test_users.py` — Role-based access control (6 new tests)
- `test_api/test_events.py` — Event RBAC (3 new tests)
- `test_api/test_courses.py` — Course RBAC (3 new tests)
- `test_utils/test_telegram_auth.py` — Generic error message verification (1 new test)

Total: **110 tests passing**.
