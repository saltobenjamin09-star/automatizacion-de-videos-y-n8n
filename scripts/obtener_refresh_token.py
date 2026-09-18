#!/usr/bin/env python3
"""Obtiene un refresh token de YouTube mediante OAuth 2.0 local.

Uso:
    python scripts/obtener_refresh_token.py --client-secret client_secret.json

El navegador se abre para autorizar la cuenta. El token se guarda en un archivo
local ignorado por Git y nunca se imprime completo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-secret", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".youtube_token.json"),
        help="Archivo local donde guardar el token (ignorado por Git).",
    )
    args = parser.parse_args()

    if not args.client_secret.exists():
        raise SystemExit(f"No existe el archivo: {args.client_secret}")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(
            "Faltan dependencias. Ejecutá: pip install -r requirements.txt"
        ) from exc

    flow = InstalledAppFlow.from_client_secrets_file(str(args.client_secret), SCOPES)
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )
    payload = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or SCOPES),
    }
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Token guardado en {args.output}.")
    print("Copiá únicamente refresh_token a YOUTUBE_REFRESH_TOKEN.")
    print("No subas ese archivo ni el client_secret.json al repositorio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
