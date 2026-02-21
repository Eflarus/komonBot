from datetime import date, time
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.models.course import Course
from src.models.event import Event
from src.services.content_page import ContentPageBuilder


@pytest.fixture
def builder():
    ghost = MagicMock()
    return ContentPageBuilder(ghost_client=ghost)


class TestBuildEventsHTML:
    def test_empty_events(self, builder):
        html = builder.build_events_html([])
        assert "Нет предстоящих мероприятий" in html

    def test_event_card_has_title(self, builder):
        event = MagicMock(spec=Event)
        event.title = "Test Event"
        event.location = "Test Venue"
        event.event_date = date(2025, 6, 15)
        event.event_time = time(19, 0)
        event.cover_image = None
        event.ticket_link = None
        html = builder.build_events_html([event])
        assert "Test Event" in html
        assert "Test Venue" in html
        assert "kg-product-card" in html

    def test_event_card_escapes_html(self, builder):
        event = MagicMock(spec=Event)
        event.title = '<script>alert("xss")</script>'
        event.location = "Venue"
        event.event_date = date(2025, 1, 1)
        event.event_time = time(12, 0)
        event.cover_image = None
        event.ticket_link = None
        html = builder.build_events_html([event])
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_event_card_with_ticket_link(self, builder):
        event = MagicMock(spec=Event)
        event.title = "Event"
        event.location = "Venue"
        event.event_date = date(2025, 1, 1)
        event.event_time = time(12, 0)
        event.cover_image = None
        event.ticket_link = "https://tickets.example.com"
        html = builder.build_events_html([event])
        assert "Купить билет" in html
        assert "https://tickets.example.com" in html

    def test_event_card_rejects_javascript_link(self, builder):
        event = MagicMock(spec=Event)
        event.title = "Event"
        event.location = "Venue"
        event.event_date = date(2025, 1, 1)
        event.event_time = time(12, 0)
        event.cover_image = None
        event.ticket_link = "javascript:alert(1)"
        html = builder.build_events_html([event])
        assert "javascript:" not in html
        assert "Купить билет" not in html


class TestBuildCoursesHTML:
    def test_empty_courses(self, builder):
        html = builder.build_courses_html([])
        assert "Нет доступных курсов" in html

    def test_course_card_has_title(self, builder):
        course = MagicMock(spec=Course)
        course.title = "Yoga Course"
        course.description = "Morning yoga"
        course.schedule = "Пн/Ср 10:00"
        course.cost = Decimal("3000")
        course.currency = "RUB"
        course.image_desktop = None
        course.image_mobile = None
        course.detailed_description = None
        html = builder.build_courses_html([course])
        assert "Yoga Course" in html
        assert "cource-card" in html
        assert "3000" in html

    def test_course_card_escapes_html(self, builder):
        course = MagicMock(spec=Course)
        course.title = '<img src=x onerror=alert(1)>'
        course.description = "Normal"
        course.schedule = "Пн"
        course.cost = Decimal("0")
        course.currency = "RUB"
        course.image_desktop = None
        course.image_mobile = None
        course.detailed_description = None
        html = builder.build_courses_html([course])
        assert "<img src=x" not in html  # raw tag must be escaped
        assert "&lt;img" in html

    def test_course_card_with_details(self, builder):
        course = MagicMock(spec=Course)
        course.title = "Course"
        course.description = "Desc"
        course.schedule = "Пн"
        course.cost = Decimal("5000")
        course.currency = "RUB"
        course.image_desktop = None
        course.image_mobile = None
        course.detailed_description = "Detailed info here"
        html = builder.build_courses_html([course])
        assert "Detailed info here" in html
        assert "Узнать подробнее" in html
