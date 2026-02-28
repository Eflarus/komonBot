# Changelog

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

- **No request body size limit** — No global limit on request body size. An attacker could send 100MB+ payloads to exhaust server memory. Added 2MB middleware limit via `Content-Length` check. (`src/main.py`)

### LOW

- **Default SECRET_KEY** — `SECRET_KEY` defaulted to `"change-me"`. Removed default (now empty string). Startup logs warnings if `SECRET_KEY` or `WEBHOOK_SECRET` are not configured. (`src/config.py`, `src/main.py`)

### Test Coverage

Added 28 new tests across `tests/test_security/`:
- `test_rate_limit.py` — IP extraction from proxy headers (6 tests)
- `test_notification_throttle.py` — Notification throttling (3 tests)
- `test_filename_sanitize.py` — UUID filename generation (6 tests)
- `test_timing_check.py` — Anti-bot timing validation (3 tests)
- `test_body_size.py` — Request size limit (3 tests)
- `test_api/test_users.py` — Role-based access control (6 new tests)
- `test_utils/test_telegram_auth.py` — Generic error message verification (1 new test)

Total: **102 tests passing**.
