#!/usr/bin/env python3
"""Genera un video MP4 didáctico a partir de escenas JSON.

El archivo no contiene material binario: crea las diapositivas con Pillow y
ensambla el MP4 con FFmpeg. Esto permite reproducir la generación en local y
en GitHub Actions sin subir un video pesado al repositorio.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "video_config.json"


def load_config(path: Path) -> dict[str, Any]:
    """Carga y valida la configuración del video."""
    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    required = {"title", "output", "duration_seconds", "fps", "width", "height", "scenes"}
    missing = sorted(required.difference(config))
    if missing:
        raise ValueError(f"Faltan campos en {path}: {', '.join(missing)}")
    if not config["scenes"]:
        raise ValueError("La configuración debe incluir al menos una escena.")

    total = sum(float(scene["duration"]) for scene in config["scenes"])
    expected = float(config["duration_seconds"])
    if abs(total - expected) > 0.01:
        raise ValueError(
            f"La duración de las escenas ({total:g}s) no coincide con "
            f"duration_seconds ({expected:g}s)."
        )
    return config


def executable(name: str, environment_name: str) -> str:
    """Devuelve la ruta de una herramienta y da un error entendible si falta."""
    configured = os.environ.get(environment_name)
    resolved = configured or shutil.which(name)
    if not resolved:
        raise RuntimeError(
            f"No se encontró {name}. Instalalo y asegurate de que esté en PATH "
            f"(o definí {environment_name})."
        )
    return resolved


def find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Busca una fuente común en Linux, Windows y macOS."""
    candidates = [
        os.environ.get("VIDEO_FONT", ""),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Convierte #RRGGBB a una tupla RGB."""
    clean = value.strip().lstrip("#")
    if len(clean) != 6:
        raise ValueError(f"Color inválido: {value!r}")
    try:
        return tuple(int(clean[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]
    except ValueError as exc:
        raise ValueError(f"Color inválido: {value!r}") from exc


def wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """Envuelve texto respetando saltos de línea y el ancho de la diapositiva."""
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            width = draw.textbbox((0, 0), candidate, font=font)[2]
            if current and width > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def render_scene(
    scene: dict[str, Any],
    destination: Path,
    width: int,
    height: int,
    scene_number: int,
    total_scenes: int,
) -> None:
    """Renderiza una escena en PNG con un diseño legible para la defensa oral."""
    accent = hex_to_rgb(str(scene.get("accent", "#2563EB")))
    background = (13, 19, 33)
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    # Bandas suaves para dar profundidad sin depender de imágenes externas.
    for x in range(width):
        blend = x / max(width - 1, 1)
        color = tuple(
            int(background[channel] * (1 - blend * 0.18) + accent[channel] * blend * 0.18)
            for channel in range(3)
        )
        draw.line((x, 0, x, height), fill=color)

    title_font = find_font(max(34, width // 25))
    body_font = find_font(max(24, width // 42))
    small_font = find_font(max(18, width // 70))
    label_font = find_font(max(16, width // 64))

    margin_x = int(width * 0.09)
    top = int(height * 0.16)
    draw.rounded_rectangle(
        (margin_x, int(height * 0.08), margin_x + 220, int(height * 0.08) + 38),
        radius=19,
        fill=accent,
    )
    draw.text(
        (margin_x + 18, int(height * 0.08) + 7),
        f"ETAPA {scene_number}/{total_scenes}",
        font=label_font,
        fill="white",
    )

    title = str(scene.get("title", "Escena"))
    title_lines = wrapped_lines(draw, title, title_font, width - 2 * margin_x)
    y = top
    for line in title_lines:
        draw.text((margin_x, y), line, font=title_font, fill="white")
        y += int(title_font.size * 1.18)

    y += int(height * 0.06)
    body = str(scene.get("body", ""))
    for line in wrapped_lines(draw, body, body_font, width - 2 * margin_x):
        draw.text((margin_x, y), line, font=body_font, fill=(222, 231, 241))
        y += int(body_font.size * 1.45)

    # Línea de acento y pie de escena para que el video sea autoexplicativo.
    line_y = int(height * 0.79)
    draw.rounded_rectangle(
        (margin_x, line_y, width - margin_x, line_y + 8),
        radius=4,
        fill=accent,
    )
    draw.text(
        (margin_x, int(height * 0.87)),
        "LOS PANCHOS TITANICOS  |  Automatización de videos y n8n",
        font=small_font,
        fill=(160, 174, 192),
    )
    image.save(destination, format="PNG", optimize=True)


def concat_path(path: Path) -> str:
    """Escapa una ruta para el formato concat de FFmpeg."""
    return str(path.resolve()).replace("'", "'\\''")


def run_ffmpeg(
    ffmpeg: str,
    concat_file: Path,
    output: Path,
    duration: float,
    fps: int,
) -> None:
    """Ensambla imágenes y una pista AAC silenciosa en un MP4 reproducible."""
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=48000:cl=stereo",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-t",
        f"{duration:.3f}",
        "-vf",
        f"fps={fps}",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "22",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg no pudo generar el video.\n"
            f"Comando: {' '.join(command)}\n"
            f"Salida: {result.stderr[-4000:]}"
        )


def inspect_video(ffprobe: str, output: Path) -> dict[str, Any]:
    """Obtiene los streams y la duración con FFprobe."""
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-show_entries",
        "stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of",
        "json",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFprobe no pudo leer {output}: {result.stderr}")
    return json.loads(result.stdout)


def validate_video(
    ffprobe: str,
    output: Path,
    expected_duration: float,
    tolerance: float = 2.0,
) -> dict[str, Any]:
    """Verifica MP4, H.264, AAC y duración aproximada."""
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(f"No se generó el archivo {output}.")
    metadata = inspect_video(ffprobe, output)
    duration = float(metadata.get("format", {}).get("duration", 0))
    streams = metadata.get("streams", [])
    video_codecs = {stream.get("codec_name") for stream in streams if stream.get("codec_type") == "video"}
    audio_codecs = {stream.get("codec_name") for stream in streams if stream.get("codec_type") == "audio"}
    if "h264" not in video_codecs:
        raise RuntimeError(f"El video no está codificado en H.264: {video_codecs}")
    if "aac" not in audio_codecs:
        raise RuntimeError(f"El audio no está codificado en AAC: {audio_codecs}")
    if abs(duration - expected_duration) > tolerance:
        raise RuntimeError(
            f"Duración inesperada: {duration:.2f}s; se esperaba "
            f"{expected_duration:.2f}s ± {tolerance:.2f}s."
        )
    return {"duration": duration, "video_codecs": sorted(video_codecs), "audio_codecs": sorted(audio_codecs)}


def generate_video(config_path: Path, output: Path, keep_frames: bool = False) -> dict[str, Any]:
    """Genera y valida el MP4. Devuelve un resumen para logs y tests."""
    config = load_config(config_path)
    ffmpeg = executable("ffmpeg", "FFMPEG_BIN")
    ffprobe = executable("ffprobe", "FFPROBE_BIN")
    width = int(config["width"])
    height = int(config["height"])
    fps = int(config["fps"])
    duration = float(config["duration_seconds"])
    scenes = config["scenes"]

    if keep_frames:
        frame_directory = ROOT / "frames"
        frame_directory.mkdir(parents=True, exist_ok=True)
        context = None
    else:
        context = tempfile.TemporaryDirectory(prefix="automatizacion_frames_")
        frame_directory = Path(context.name)

    try:
        concat_file = frame_directory / "concat.txt"
        with concat_file.open("w", encoding="utf-8") as file:
            for index, scene in enumerate(scenes, start=1):
                frame = frame_directory / f"scene_{index:02d}.png"
                render_scene(scene, frame, width, height, index, len(scenes))
                file.write(f"file '{concat_path(frame)}'\n")
                file.write(f"duration {float(scene['duration']):.3f}\n")
            # El demuxer concat conserva la duración de la última entrada
            # cuando se repite explícitamente el último archivo.
            last_frame = frame_directory / f"scene_{len(scenes):02d}.png"
            file.write(f"file '{concat_path(last_frame)}'\n")

        run_ffmpeg(ffmpeg, concat_file, output, duration, fps)
        summary = validate_video(ffprobe, output, duration)
        summary["output"] = str(output)
        return summary
    finally:
        if context is not None:
            context.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, help="Ruta de salida; por defecto usa config.output.")
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Conserva los PNG temporales en la carpeta frames/.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    output = args.output or ROOT / str(config["output"])
    summary = generate_video(args.config, output, keep_frames=args.keep_frames)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
