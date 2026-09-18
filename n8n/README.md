# Workflow de n8n

El archivo **recordatorio_pastilla.json** es importable en una instalación local de n8n. El flujo tiene tres pasos:

1. El nodo Cron se dispara a las 12:00 y a las 19:00.
2. El nodo **Preparar mensaje** crea exactamente el texto **RECUERDA TOMAR LA PASTILLA**.
3. El nodo Telegram lo envía al chat indicado por **N8N_TELEGRAM_CHAT_ID**.

## Configuración

1. En n8n, abrí **Settings > Import from File** e importá **recordatorio_pastilla.json**.
2. Configurá la zona horaria del proceso n8n como **America/Argentina/Buenos_Aires**. En Docker se puede definir **GENERIC_TIMEZONE=America/Argentina/Buenos_Aires**.
3. Creá una credencial de Telegram Bot en el nodo **Enviar por Telegram**.
4. Definí **N8N_TELEGRAM_CHAT_ID** en el entorno de n8n o reemplazá la expresión del campo **Chat ID** por tu identificador.
5. Guardá, probá el nodo manualmente y activá el workflow.

El JSON no contiene tokens ni credenciales reales. El workflow queda inactivo al importarlo para que puedas revisar el destinatario antes de activarlo.
