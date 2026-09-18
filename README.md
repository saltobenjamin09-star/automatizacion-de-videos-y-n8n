# Automatización de videos y n8n

Proyecto académico del grupo **LOS PANCHOS TITANICOS**. Integra generación de video con Python y FFmpeg, publicación programada en YouTube mediante OAuth 2.0 y un workflow local de n8n para recordatorios.

## Qué resuelve

- Genera localmente un MP4 de 5:30 minutos.
- Codifica video H.264 y audio AAC.
- Comprueba duración y codecs con FFprobe.
- Ejecuta pruebas automatizadas con pytest.
- Repite la generación en GitHub Actions y conserva el MP4 como artifact.
- Sube el video a YouTube como privado y lo programa para las 21:00 de Argentina.
- Ejecuta en n8n un recordatorio a las 12:00 y a las 19:00 con el texto **RECUERDA TOMAR LA PASTILLA**.

El archivo MP4 no se versiona porque es un artefacto generado. El código y la configuración permiten reconstruirlo en cualquier ejecución.

## Estructura

    src/generar_video.py              Genera y valida las escenas del MP4
    src/subir_youtube.py              OAuth, payload y carga a YouTube
    scripts/obtener_refresh_token.py  Autorización OAuth local
    scripts/verificar_video.py        Verificación independiente con FFprobe
    config/video_config.json          Título, escenas, duración y horario
    .github/workflows/publicar_youtube.yml
                                      Workflow manual y programado
    n8n/recordatorio_pastilla.json    Workflow importable en n8n
    tests/                             Pruebas de configuración y publicación
    docs/                              Guías de YouTube y defensa oral

## Ejecución local

Requisitos: Python 3.10 o superior y FFmpeg con FFprobe disponibles en PATH.

    python -m venv .venv

En Windows:

    .venv\Scripts\activate

En Linux/macOS:

    source .venv/bin/activate

Instalá dependencias y ejecutá el flujo:

    python -m pip install -r requirements.txt
    python -m pytest
    python src/generar_video.py
    python scripts/verificar_video.py dist/automatizacion_videos_n8n.mp4

La generación produce exactamente 330 segundos (5:30), dentro del rango de evaluación de 5 a 6 minutos. Las diapositivas se crean con Pillow y FFmpeg las ensambla con una pista AAC silenciosa para mantener un archivo reproducible.

## Publicación en YouTube

La guía completa está en **docs/CONFIGURAR_YOUTUBE.md**. El flujo usa únicamente el scope:

    https://www.googleapis.com/auth/youtube.upload

Para una prueba segura del payload, sin contactar la API:

    python src/subir_youtube.py --video dist/automatizacion_videos_n8n.mp4 --dry-run

En GitHub, configurá estos Secrets:

- YOUTUBE_CLIENT_ID
- YOUTUBE_CLIENT_SECRET
- YOUTUBE_REFRESH_TOKEN

El workflow ejecuta cada día a las 20:30 de Argentina (23:30 UTC), genera y valida el MP4, lo guarda como artifact y lo sube como privado con publishAt a las 21:00. También puede ejecutarse desde **Actions > Generar y programar video en YouTube > Run workflow** indicando una fecha ISO 8601 opcional.

## n8n

Importá **n8n/recordatorio_pastilla.json**, definí la zona horaria **America/Argentina/Buenos_Aires**, seleccioná la credencial de Telegram y configurá **N8N_TELEGRAM_CHAT_ID**. El workflow queda inactivo al importarlo para revisar el destinatario antes de activarlo. La guía está en **n8n/README.md**.

## Seguridad

- No subas archivos .env, client_secret.json, refresh tokens ni credenciales de Telegram.
- Los valores sensibles solo se leen desde el entorno.
- Si una credencial se expone, revocala y generá otra.
- El repositorio contiene placeholders y documentación, nunca secretos reales.

## Estado de la rúbrica

- [x] Repositorio público y estructura inicial.
- [x] Script Python que genera MP4 local.
- [x] Duración y codecs verificables con FFprobe.
- [x] Workflow de GitHub Actions con ejecución manual y cron.
- [x] OAuth 2.0, refresh token y secrets documentados.
- [x] Programación de YouTube a las 21:00 de Argentina.
- [x] Workflow n8n con recordatorios de 12:00 y 19:00.
- [x] Pruebas y guion para la defensa oral.
