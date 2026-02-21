from datetime import date


def make_event(**kwargs) -> dict:
    """Default event creation data."""
    defaults = {
        "title": "Test Event",
        "description": "Test description",
        "location": "Test Venue",
        "event_date": str(date(2025, 6, 15)),
        "event_time": "19:00",
        "order": 0,
    }
    defaults.update(kwargs)
    return defaults


def make_course(**kwargs) -> dict:
    """Default course creation data."""
    defaults = {
        "title": "Test Course",
        "description": "Test course description",
        "schedule": "Пн/Ср 19:00-20:30",
        "cost": 5000,
        "currency": "RUB",
        "order": 0,
    }
    defaults.update(kwargs)
    return defaults


def make_contact(**kwargs) -> dict:
    """Default contact submission data."""
    defaults = {
        "name": "Test Person",
        "phone": "+7 999 123 4567",
        "message": "Test message text",
        "source": "site",
    }
    defaults.update(kwargs)
    return defaults


def make_user(**kwargs) -> dict:
    """Default user creation data."""
    defaults = {
        "telegram_id": 987654321,
        "username": "newuser",
        "first_name": "New",
    }
    defaults.update(kwargs)
    return defaults
