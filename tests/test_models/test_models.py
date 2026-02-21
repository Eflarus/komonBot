from src.models.course import CourseStatus
from src.models.event import EventStatus


class TestEnums:
    def test_event_status_values(self):
        assert EventStatus.DRAFT == "draft"
        assert EventStatus.PUBLISHED == "published"
        assert EventStatus.CANCELLED == "cancelled"
        assert EventStatus.ARCHIVED == "archived"

    def test_course_status_values(self):
        assert CourseStatus.DRAFT == "draft"
        assert CourseStatus.PUBLISHED == "published"
        assert CourseStatus.CANCELLED == "cancelled"
        assert CourseStatus.ARCHIVED == "archived"

    def test_event_status_is_string(self):
        assert isinstance(EventStatus.DRAFT, str)

    def test_course_status_is_string(self):
        assert isinstance(CourseStatus.DRAFT, str)
