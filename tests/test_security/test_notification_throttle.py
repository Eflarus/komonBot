import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.notification import CONTACT_NOTIFY_INTERVAL, NotificationService


@pytest.fixture
def service():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    svc = NotificationService(bot)
    return svc


class TestContactNotificationThrottle:
    async def test_first_notification_sent(self, service):
        with patch(
            "src.services.notification.async_session_factory"
        ) as mock_sf:
            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: []))
            )
            with patch(
                "src.services.notification.UserRepository"
            ) as mock_repo_cls:
                mock_repo_cls.return_value.get_all_telegram_ids = AsyncMock(
                    return_value=[111]
                )
                await service.notify_contact_submission("test msg")

        service.bot.send_message.assert_called_once_with(111, "test msg")

    async def test_second_notification_throttled(self, service):
        with patch(
            "src.services.notification.async_session_factory"
        ) as mock_sf:
            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            with patch(
                "src.services.notification.UserRepository"
            ) as mock_repo_cls:
                mock_repo_cls.return_value.get_all_telegram_ids = AsyncMock(
                    return_value=[111]
                )

                await service.notify_contact_submission("msg 1")
                await service.notify_contact_submission("msg 2")

        # Only 1 call — second was throttled
        assert service.bot.send_message.call_count == 1
        assert service._suppressed_count == 1

    async def test_notification_sent_after_interval(self, service):
        with patch(
            "src.services.notification.async_session_factory"
        ) as mock_sf:
            mock_session = AsyncMock()
            mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            with patch(
                "src.services.notification.UserRepository"
            ) as mock_repo_cls:
                mock_repo_cls.return_value.get_all_telegram_ids = AsyncMock(
                    return_value=[111]
                )

                await service.notify_contact_submission("msg 1")

                # Simulate time passing
                service._last_contact_notify = (
                    time.monotonic() - CONTACT_NOTIFY_INTERVAL - 1
                )
                service._suppressed_count = 3

                await service.notify_contact_submission("msg 2")

        assert service.bot.send_message.call_count == 2
        # Second message should include suppressed count
        second_call_msg = service.bot.send_message.call_args_list[1][0][1]
        assert "+3" in second_call_msg
        assert service._suppressed_count == 0
