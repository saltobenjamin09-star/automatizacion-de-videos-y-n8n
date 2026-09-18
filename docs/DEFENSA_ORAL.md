# Guion para la defensa oral

## Idea principal

El proyecto automatiza una cadena completa: Python crea un video, FFmpeg lo codifica, GitHub Actions repite el proceso en la nube, la API de YouTube lo programa y n8n envía recordatorios independientes.

## Recorrido recomendado

1. Mostrar el árbol del repositorio y explicar por qué el video generado no se versiona como binario.
2. Abrir **config/video_config.json** y señalar la duración total de 330 segundos, las seis escenas y el horario de publicación.
3. Ejecutar **python src/generar_video.py** y explicar que Pillow dibuja las diapositivas y FFmpeg genera H.264/AAC.
4. Ejecutar **python scripts/verificar_video.py dist/automatizacion_videos_n8n.mp4** y mostrar duración y codecs.
5. Abrir el workflow de GitHub Actions y explicar checkout, Python, FFmpeg, generación, validación, artifact y secrets.
6. Explicar OAuth 2.0: el client ID y el client secret identifican la aplicación; el refresh token permite obtener access tokens sin guardar una contraseña; el scope limita el permiso a subir videos.
7. Mostrar **src/subir_youtube.py** y explicar que el video se sube como privado con publishAt en UTC, calculado desde las 21:00 de Argentina.
8. Importar el JSON de n8n, revisar los dos cron y el mensaje exacto, seleccionar la credencial de Telegram y activar después de comprobar el chat.

## Preguntas que pueden hacer

### ¿Por qué no se sube el MP4 al repositorio?

Porque es un artefacto generado, puede pesar mucho y se reproduce desde el código y la configuración. GitHub Actions conserva una copia como artifact.

### ¿Por qué el video queda privado antes de las 21:00?

YouTube exige que un video programado tenga privacyStatus privado y un publishAt futuro. La plataforma cambia el estado automáticamente en la fecha indicada.

### ¿Dónde están las credenciales?

En variables de entorno locales o en GitHub Secrets. Nunca en JSON, código fuente ni commits.

### ¿Qué ocurre si se ejecuta el workflow manualmente?

Se puede indicar publish_at. Si se deja vacío, el programa calcula la próxima hora configurada y evita una fecha demasiado cercana para que YouTube la acepte.

### ¿Qué hace n8n?

El nodo Cron inicia dos ejecuciones diarias, el nodo Set prepara el texto y Telegram lo envía. La zona horaria se configura en el entorno n8n.

## Evidencias para mostrar

- Un commit inicial del repositorio.
- La salida de pytest.
- La salida de FFprobe.
- Una ejecución exitosa de GitHub Actions.
- El artifact MP4 descargable.
- El workflow n8n importado y una ejecución de prueba.
