#!/usr/bin/env python3
"""Verifica duración y codecs de un MP4 usando FFprobe."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--min-seconds", type=float, default=320)
    parser.add_argument("--max-seconds", type=float, default=360)
    args = parser.parse_args()

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SystemExit("No se encontró ffprobe en PATH.")
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-show_entries",
        "stream=codec_type,codec_name,width,height",
        "-of",
        "json",
        str(args.video),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(result.stderr)
    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])
    streams = data.get("streams", [])
    codecs = {stream.get("codec_name") for stream in streams}
    if not args.min_seconds <= duration <= args.max_seconds:
        raise SystemExit(
            f"Duración fuera de rango: {duration:.2f}s; "
            f"se esperaba entre {args.min_seconds:g}s y {args.max_seconds:g}s."
        )
    required = {"h264", "aac"}
    if not required.issubset(codecs):
        raise SystemExit(f"Codecs incompletos: {sorted(codecs)}")
    print(json.dumps({"duration": duration, "codecs": sorted(codecs), "streams": streams}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
