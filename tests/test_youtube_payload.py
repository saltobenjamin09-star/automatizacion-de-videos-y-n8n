from datetime import datetime, timezone

from src.subir_youtube import build_request_body


def test_scheduled_payload_is_private_and_has_publish_at():
    config = {
        "title": "Video de prueba",
        "description": "Descripción",
        "tags": ["Python"],
        "category_id": "27",
    }
    body = build_request_body(
        config, datetime(2026, 9, 19, 0, 0, tzinfo=timezone.utc)
    )
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == "2026-09-19T00:00:00Z"
    assert body["snippet"]["categoryId"] == "27"
