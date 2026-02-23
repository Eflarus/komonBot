import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.services.backup import (
    create_backup,
    rotate_backups,
    run_backup,
    send_backup_to_telegram,
)


@pytest.fixture
def backup_dir(tmp_path):
    with patch("src.services.backup.settings") as mock_settings:
        mock_settings.BACKUP_DIR = str(tmp_path / "backups")
        mock_settings.BACKUP_KEEP = 3
        mock_settings.TIMEZONE = "UTC"
        mock_settings.DATABASE_URL = f"sqlite+aiosqlite:///{tmp_path}/test.db"
        mock_settings.BACKUP_TELEGRAM_IDS = [111, 222]

        # Create a real source database with a table and data
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'hello')")
        conn.commit()
        conn.close()

        yield tmp_path


class TestCreateBackup:
    def test_creates_backup_file(self, backup_dir):
        path = create_backup()
        assert path.exists()
        assert path.name.startswith("komonbot-")
        assert path.suffix == ".db"

    def test_backup_contains_data(self, backup_dir):
        path = create_backup()
        conn = sqlite3.connect(str(path))
        rows = conn.execute("SELECT val FROM test").fetchall()
        conn.close()
        assert rows == [("hello",)]

    def test_creates_backup_dir_if_missing(self, backup_dir):
        backup_path = Path(backup_dir) / "backups"
        assert not backup_path.exists()
        create_backup()
        assert backup_path.exists()


class TestRotateBackups:
    def test_keeps_only_n_newest(self, backup_dir):
        backup_path = Path(backup_dir) / "backups"
        backup_path.mkdir(parents=True)

        # Create 5 backup files with different names (sorted by name = sorted by time)
        for i in range(5):
            (backup_path / f"komonbot-2026010{i}-040000.db").touch()

        removed = rotate_backups()
        assert removed == 2
        remaining = sorted(backup_path.glob("komonbot-*.db"))
        assert len(remaining) == 3
        # Oldest two should be removed
        assert remaining[0].name == "komonbot-20260102-040000.db"

    def test_no_removal_when_under_limit(self, backup_dir):
        backup_path = Path(backup_dir) / "backups"
        backup_path.mkdir(parents=True)

        (backup_path / "komonbot-20260101-040000.db").touch()
        (backup_path / "komonbot-20260102-040000.db").touch()

        removed = rotate_backups()
        assert removed == 0
        assert len(list(backup_path.glob("komonbot-*.db"))) == 2

    def test_no_error_when_dir_missing(self, backup_dir):
        removed = rotate_backups()
        assert removed == 0


class TestRunBackup:
    @pytest.mark.asyncio
    async def test_creates_and_rotates(self, backup_dir):
        path = await run_backup()
        assert path.exists()
        assert path.name.startswith("komonbot-")


class TestSendBackupToTelegram:
    @pytest.mark.asyncio
    async def test_sends_to_all_configured_ids(self, backup_dir):
        bot = MagicMock()
        bot.send_document = AsyncMock()

        await send_backup_to_telegram(bot)

        assert bot.send_document.call_count == 2
        call_ids = [
            call.kwargs["chat_id"]
            for call in bot.send_document.call_args_list
        ]
        assert call_ids == [111, 222]

    @pytest.mark.asyncio
    async def test_skips_when_no_ids_configured(self, backup_dir):
        with patch("src.services.backup.settings") as mock_settings:
            mock_settings.BACKUP_TELEGRAM_IDS = []
            mock_settings.TIMEZONE = "UTC"

            bot = MagicMock()
            bot.send_document = AsyncMock()

            await send_backup_to_telegram(bot)
            bot.send_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_continues_on_send_failure(self, backup_dir):
        bot = MagicMock()
        bot.send_document = AsyncMock(
            side_effect=[Exception("network error"), None]
        )

        # Should not raise, should try both IDs
        await send_backup_to_telegram(bot)
        assert bot.send_document.call_count == 2
