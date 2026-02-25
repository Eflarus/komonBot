import asyncio
from urllib.parse import urlparse

import structlog
from markupsafe import escape

from src.config import settings
from src.database import async_session_factory
from src.models.course import Course
from src.models.event import Event
from src.repositories.course import CourseRepository
from src.repositories.event import EventRepository
from src.services.ghost import GhostClient

logger = structlog.get_logger()

CURRENCY_SYMBOLS = {"RUB": "\u20bd", "USD": "$", "EUR": "\u20ac"}

MONTHS_RU = {
    1: "\u044f\u043d\u0432\u0430\u0440\u044f",
    2: "\u0444\u0435\u0432\u0440\u0430\u043b\u044f",
    3: "\u043c\u0430\u0440\u0442\u0430",
    4: "\u0430\u043f\u0440\u0435\u043b\u044f",
    5: "\u043c\u0430\u044f",
    6: "\u0438\u044e\u043d\u044f",
    7: "\u0438\u044e\u043b\u044f",
    8: "\u0430\u0432\u0433\u0443\u0441\u0442\u0430",
    9: "\u0441\u0435\u043d\u0442\u044f\u0431\u0440\u044f",
    10: "\u043e\u043a\u0442\u044f\u0431\u0440\u044f",
    11: "\u043d\u043e\u044f\u0431\u0440\u044f",
    12: "\u0434\u0435\u043a\u0430\u0431\u0440\u044f",
}


def _format_date_ru(d) -> str:
    if not d:
        return ""
    return f"{d.day} {MONTHS_RU.get(d.month, '')} {d.year}"


def _format_time(t) -> str:
    if not t:
        return ""
    return t.strftime("%H:%M")


def _currency_symbol(code: str) -> str:
    return CURRENCY_SYMBOLS.get(code, code)


def _safe_url(url: str | None) -> str | None:
    """Validate URL scheme — only allow http/https."""
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    return url


def _format_title_html(title: str) -> str:
    """Split title by newlines into <span><br><span> pairs matching Ghost card format."""
    parts = str(escape(title)).split("\n")
    return "<br>".join(
        f'<span style="white-space: pre-wrap;">{p}</span>' for p in parts
    )


class ContentPageBuilder:
    """Builds HTML from published entities and pushes to Ghost pages."""

    def __init__(self, ghost_client: GhostClient, notification_service=None):
        self.ghost_client = ghost_client
        self.notification_service = notification_service
        self._events_lock = asyncio.Lock()
        self._courses_lock = asyncio.Lock()

    def build_events_html(self, events: list[Event]) -> str:
        """Render all event cards wrapped in container div."""
        if not events:
            return "<p>Нет предстоящих мероприятий</p>"
        cards = "\n".join(self._render_event_card(e) for e in events)
        return f'<div class="col3 kg-width-wide">\n{cards}\n</div>'

    def build_courses_html(self, courses: list[Course]) -> str:
        """Render all course cards wrapped in container div."""
        if not courses:
            return "<p>Нет доступных курсов</p>"
        cards = "\n".join(self._render_course_card(c) for c in courses)
        return f'<div class="col3 kg-width-wide">\n{cards}\n</div>'

    def _render_event_card(self, event: Event) -> str:
        """Single event -> kg-product-card HTML. All user input escaped."""
        title_html = _format_title_html(event.title)
        location = escape(event.location)
        date_formatted = escape(_format_date_ru(event.event_date))
        time_formatted = escape(_format_time(event.event_time))

        image_html = ""
        if event.cover_image:
            img_url = escape(event.cover_image)
            image_html = (
                f'        <img src="{img_url}" width="516" height="516"\n'
                f'             class="kg-product-card-image" loading="lazy">'
            )

        ticket_html = ""
        safe_link = _safe_url(event.ticket_link)
        if safe_link:
            link = escape(safe_link)
            ticket_html = (
                f'        <a href="{link}" '
                f'class="kg-product-card-button kg-product-card-btn-accent"\n'
                f'           target="_blank" rel="noopener noreferrer">\n'
                f"            <span>\u041a\u0443\u043f\u0438\u0442\u044c "
                f"\u0431\u0438\u043b\u0435\u0442</span>\n"
                f"        </a>"
            )

        return (
            f'<div class="kg-card kg-product-card">\n'
            f'    <div class="kg-product-card-container">\n'
            f"{image_html}\n"
            f'        <div class="kg-product-card-title-container">\n'
            f'            <h4 class="kg-product-card-title">{title_html}</h4>\n'
            f"        </div>\n"
            f'        <div class="kg-product-card-description">\n'
            f"            <p>\n"
            f'                <span style="white-space: pre-wrap;">{location}</span><br>\n'
            f'                <span style="white-space: pre-wrap;">{date_formatted}</span><br>\n'
            f'                <span style="white-space: pre-wrap;">{time_formatted}</span>\n'
            f"            </p>\n"
            f"        </div>\n"
            f"{ticket_html}\n"
            f"    </div>\n"
            f"</div>"
        )

    def _render_course_card(self, course: Course) -> str:
        """Single course -> cource-card HTML. All user input escaped."""
        title = escape(course.title)
        title_html = _format_title_html(course.title)
        description = escape(course.description)
        schedule = escape(course.schedule)
        cost = escape(str(course.cost))
        symbol = escape(_currency_symbol(course.currency))

        desktop_img = ""
        if course.image_desktop:
            img_url = escape(course.image_desktop)
            desktop_img = f'    <img class="smh" src="{img_url}" alt="{title}">'

        mobile_img = ""
        if course.image_mobile:
            img_url = escape(course.image_mobile)
            mobile_img = f'    <img class="pch" src="{img_url}" alt="{title}">'

        detailed_html = ""
        if course.detailed_description:
            detailed = escape(course.detailed_description)
            detailed_html = f"            <div><p>{detailed}</p></div>"

        return (
            f'<div class="cource-card">\n'
            f"{desktop_img}\n"
            f"{mobile_img}\n"
            f'    <span class="price">{cost} {symbol}</span>\n'
            f'    <div class="cource-desc">\n'
            f'        <h3 class="cource-header">{title_html}</h3>\n'
            f'        <p class="long-text smh">{description}</p>\n'
            f'        <details class="cource-more">\n'
            f"            <summary><button type=\"button\">"
            f"\u0423\u0437\u043d\u0430\u0442\u044c "
            f"\u043f\u043e\u0434\u0440\u043e\u0431\u043d\u0435\u0435"
            f"</button></summary>\n"
            f"            <h4>\u0414\u0430\u0442\u044b</h4>\n"
            f"            <p>{schedule}</p>\n"
            f"{detailed_html}\n"
            f"        </details>\n"
            f"    </div>\n"
            f"</div>"
        )

    async def sync_events_page(self) -> None:
        """Fetch PUBLISHED events -> build HTML -> PUT to Ghost page."""
        async with self._events_lock:
            try:
                async with async_session_factory() as session:
                    repo = EventRepository(session)
                    events = await repo.get_published()

                html = self.build_events_html(events)
                await self.ghost_client.update_page_html(
                    settings.GHOST_EVENTS_PAGE_ID, html
                )
                logger.info("Events page synced", count=len(events))
            except Exception:
                logger.exception("Ghost sync failed for events page")
                if self.notification_service:
                    try:
                        await self.notification_service.notify_admins(
                            "Ghost sync FAILED for events page. Manual check required."
                        )
                    except Exception:
                        pass
                raise

    async def sync_courses_page(self) -> None:
        """Fetch PUBLISHED courses -> build HTML -> PUT to Ghost page."""
        async with self._courses_lock:
            try:
                async with async_session_factory() as session:
                    repo = CourseRepository(session)
                    courses = await repo.get_published()

                html = self.build_courses_html(courses)
                await self.ghost_client.update_page_html(
                    settings.GHOST_COURSES_PAGE_ID, html
                )
                logger.info("Courses page synced", count=len(courses))
            except Exception:
                logger.exception("Ghost sync failed for courses page")
                if self.notification_service:
                    try:
                        await self.notification_service.notify_admins(
                            "Ghost sync FAILED for courses page. Manual check required."
                        )
                    except Exception:
                        pass
                raise
