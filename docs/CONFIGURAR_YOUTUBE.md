# Configuración de YouTube y OAuth 2.0

La publicación está implementada en **src/subir_youtube.py** con el alcance mínimo:

    https://www.googleapis.com/auth/youtube.upload

No hay claves, refresh tokens ni archivos de Google dentro del repositorio.

## 1. Crear credenciales

1. Abrí Google Cloud Console y creá o seleccioná un proyecto.
2. Habilitá **YouTube Data API v3**.
3. Configurá la pantalla de consentimiento OAuth.
4. Creá un cliente OAuth de tipo **Desktop app** y descargá el JSON como **client_secret.json**.
5. Instalá las dependencias del repositorio:

       python -m pip install -r requirements.txt

6. Ejecutá el flujo de autorización local:

       python scripts/obtener_refresh_token.py --client-secret client_secret.json

El navegador pedirá autorización para la cuenta dueña del canal. El script guarda un archivo local ignorado por Git y muestra qué variable completar; nunca sube el token.

## 2. Probar localmente

Definí estas variables en la terminal o en un archivo **.env** cargado por tu herramienta:

    YOUTUBE_CLIENT_ID
    YOUTUBE_CLIENT_SECRET
    YOUTUBE_REFRESH_TOKEN

Generá y validá el MP4:

    python src/generar_video.py
    python scripts/verificar_video.py dist/automatizacion_videos_n8n.mp4

Probá el payload sin llamar a YouTube:

    python src/subir_youtube.py --video dist/automatizacion_videos_n8n.mp4 --dry-run

Para elegir una fecha concreta, usá ISO 8601 con zona:

    python src/subir_youtube.py --video dist/automatizacion_videos_n8n.mp4 --publish-at 2026-09-18T21:00:00-03:00

## 3. Configurar GitHub Actions

En **Settings > Secrets and variables > Actions**, agregá los secretos:

- YOUTUBE_CLIENT_ID
- YOUTUBE_CLIENT_SECRET
- YOUTUBE_REFRESH_TOKEN

El workflow también permite una entrada opcional **publish_at** cuando se ejecuta manualmente. Si queda vacía, calcula el próximo día a las 21:00 en **America/Argentina/Buenos_Aires**.

El cron del workflow es **30 23 * * ***: se ejecuta a las 20:30 de Argentina (UTC-3), genera el video y lo sube como privado con **publishAt** a las 21:00. YouTube lo publica automáticamente en ese horario.

## Seguridad

- No pegues secretos en issues, commits, README ni capturas.
- Si un token se expone, revocalo en Google Cloud y generá uno nuevo.
- El repositorio solo contiene nombres de variables y documentación.
