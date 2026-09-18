from datetime import datetime
from zoneinfo import ZoneInfo

from src.subir_youtube import format_rfc3339, next_publication_time


ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")


def test_publication_at_21_same_day_when_there_is_time():
    now = datetime(2026, 9, 18, 10, 0, tzinfo=ARGENTINA)
    result = next_publication_time(now=now)
    assert result.astimezone(ARGENTINA).strftime("%Y-%m-%d %H:%M") == "2026-09-18 21:00"


def test_publication_moves_to_next_day_after_target():
    now = datetime(2026, 9, 18, 22, 0, tzinfo=ARGENTINA)
    result = next_publication_time(now=now)
    assert result.astimezone(ARGENTINA).strftime("%Y-%m-%d %H:%M") == "2026-09-19 21:00"


def test_rfc3339_is_utc():
    value = datetime(2026, 9, 18, 21, 0, tzinfo=ARGENTINA)
    assert format_rfc3339(value) == "2026-09-19T00:00:00Z"
