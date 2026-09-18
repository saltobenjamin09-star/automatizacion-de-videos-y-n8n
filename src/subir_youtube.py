#!/usr/bin/env python3
"""Sube y programa un video usando YouTube Data API v3 y OAuth 2.0.

Las credenciales se leen exclusivamente desde variables de entorno. El
refresh token nunca se imprime y debe guardarse como secreto de GitHub o en un
archivo .env local que no se suba al repositorio.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "video_config.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_local_time(value: str) -> tuple[int, int]:
    try:
        hour_text, minute_text = value.strip().split(":", 1)
        hour, minute = int(hour_text), int(minute_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Hora inválida: {value!r}. Usá el formato HH:MM.") from exc
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(f"Hora inválida: {value!r}.")
    return hour, minute


def parse_publish_at(value: str, timezone_name: str) -> datetime:
    """Interpreta ISO 8601; si no hay zona, usa la zona de Argentina."""
    clean = value.strip()
    if not clean:
        raise ValueError("publish_at no puede estar vacío.")
    candidate = clean.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(
            f"Fecha inválida: {value!r}. Usá, por ejemplo, "
            "2026-09-18T21:00:00-03:00."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return parsed


def next_publication_time(
    now: datetime | None = None,
    local_time: str = "21:00",
    timezone_name: str = "America/Argentina/Buenos_Aires",
    minimum_lead_minutes: int = 10,
) -> datetime:
    """Calcula el próximo horario de publicación en UTC.

    YouTube necesita que publishAt sea futuro. Por eso, si el workflow empieza
    demasiado cerca de las 21:00, se elige el día siguiente.
    """
    local_zone = ZoneInfo(timezone_name)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=local_zone)
    current_local = current.astimezone(local_zone)
    hour, minute = parse_local_time(local_time)
    target_local = current_local.replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if target_local <= current_local + timedelta(minutes=minimum_lead_minutes):
        target_local += timedelta(days=1)
    return target_local.astimezone(timezone.utc)


def format_rfc3339(value: datetime) -> str:
    """Formatea una fecha UTC como exige la API de YouTube."""
    if value.tzinfo is None:
        raise ValueError("La fecha debe tener zona horaria.")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_status(
    config: dict[str, Any],
    publish_at: datetime | None,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "privacyStatus": "private" if publish_at else "private",
        "selfDeclaredMadeForKids": False,
    }
    if publish_at:
        status["publishAt"] = format_rfc3339(publish_at)
    return status


def build_request_body(
    config: dict[str, Any],
    publish_at: datetime | None,
) -> dict[str, Any]:
    """Construye el payload sin incluir secretos."""
    snippet = {
        "title": str(config["title"]),
        "description": str(config.get("description", "")),
        "tags": list(config.get("tags", [])),
        "categoryId": str(config.get("category_id", "27")),
    }
    return {"snippet": snippet, "status": build_status(config, publish_at)}


def build_credentials():
    """Crea credenciales OAuth con refresh token sin mostrarlo en logs."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "Faltan dependencias de Google. Ejecutá: pip install -r requirements.txt"
        ) from exc

    missing = [
        name
        for name in (
            "YOUTUBE_CLIENT_ID",
            "YOUTUBE_CLIENT_SECRET",
            "YOUTUBE_REFRESH_TOKEN",
        )
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(
            "Faltan variables de entorno requeridas: "
            + ", ".join(missing)
            + ". Configuralas localmente o en GitHub Secrets."
        )

    credentials = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri=TOKEN_URI,
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    credentials.refresh(Request())
    return credentials


def upload_video(
    video_path: Path,
    config_path: Path = DEFAULT_CONFIG,
    publish_at: datetime | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Sube el archivo o devuelve el payload en modo de prueba."""
    if not video_path.exists():
        raise FileNotFoundError(f"No existe el video: {video_path}")
    config = load_config(config_path)
    body = build_request_body(config, publish_at)

    if dry_run:
        return {"dry_run": True, "body": body, "video": str(video_path)}

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError(
            "Faltan dependencias de Google. Ejecutá: pip install -r requirements.txt"
        ) from exc

    credentials = build_credentials()
    youtube = build("youtube", "v3", credentials=credentials)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=-1,
            resumable=True,
        ),
    )
    response = request.execute()
    video_id = response["id"]
    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "publish_at": body["status"].get("publishAt"),
        "privacy_status": body["status"]["privacyStatus"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--publish-at",
        help="ISO 8601. Si se omite, se calcula el próximo día a la hora configurada.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida el payload sin contactar a YouTube.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    timezone_name = str(config.get("timezone", "America/Argentina/Buenos_Aires"))
    publish_value = args.publish_at or os.environ.get("YOUTUBE_PUBLISH_AT", "")
    if publish_value:
        publish_at = parse_publish_at(publish_value, timezone_name)
    else:
        publish_at = next_publication_time(
            local_time=str(config.get("publish_local_time", "21:00")),
            timezone_name=timezone_name,
        )

    result = upload_video(
        args.video,
        config_path=args.config,
        publish_at=publish_at,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
