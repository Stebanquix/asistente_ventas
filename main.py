import os
import json
import requests
from fastapi import FastAPI, Request, Response, HTTPException
from google import genai
from google.genai import types

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y VARIABLES DE ENTORNO
# ------------------------------------------------------------------------------
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "PistasPro2026")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Token de acceso de Meta
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")  # Phone Number ID de WhatsApp
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inicialización del cliente oficial de Google GenAI
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="Chatbot Pistas Musicales Colombia")

# Prompt del sistema para el asistente comercial
SYSTEM_INSTRUCTION = """
Eres un asistente comercial automatizado, servicial y profesional para un negocio de pistas musicales instrumentales en Colombia.
Tu tono es ultra-neutral, cortés y claro.

TARIFA Y PRODUCTOS:
- Pistas instrumentales en formato MP3: $20.000 COP cada una.
- Pistas instrumentales en formato WAV: $30.000 COP cada una.

DESCUENTOS Y COMBOS (Manejo controlado de precios):
- Si el cliente compra 3 o más pistas en MP3, el precio baja a $15.000 COP por unidad.
- Si el cliente compra 3 o más pistas en WAV, el precio baja a $25.000 COP por unidad.
- Para pedidos personalizados o negociaciones especiales, mantén la cordialidad y redirige al cierre de venta.

ENLACE DE CONTACTO Y PAGO:
Cuando el cliente confirme su pedido o solicite hablar con un asesor/realizar el pago, comparte el siguiente enlace directo de WhatsApp:
https://wa.link

Instrucciones de respuesta:
- Sé conciso, amable y directo.
- Responde siempre con los precios en pesos colombianos ($ COP).
"""

# ------------------------------------------------------------------------------
# 2. ENDPOINT DE VERIFICACIÓN DEL WEBHOOK (GET)
# ------------------------------------------------------------------------------
@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Endpoint requerido por Meta para validar la Callback URL.
    Debe devolver obligatoriamente el parámetro 'hub.challenge' en texto plano (plain text).
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            # Retorno en texto plano exigido por Meta
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Token de verificación inválido")
            
    raise HTTPException(status_code=400, detail="Parámetros faltantes")

# ------------------------------------------------------------------------------
# 3. ENDPOINT DE PROCESAMIENTO DE MENSAJES (POST)
# ------------------------------------------------------------------------------
@app.post("/webhook")
async def receive_message(request: Request):
    """
    Recibe los eventos enviados por Meta cuando un usuario escribe por WhatsApp.
    """
    data = await request.json()

    try:
        # Extraer estructura del mensaje entrante de la API Graph
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            message = messages[0]
            from_number = message.get("from")  # Número del cliente
            msg_type = message.get("type")

            # Procesar mensajes de texto
            if msg_type == "text":
                user_text = message.get("text", {}).get("body", "")

                # Generar respuesta con Gemini 2.5 Flash / 3.8 Flash
                bot_response = generate_gemini_response(user_text)

                # Enviar respuesta al usuario vía WhatsApp Cloud API
                send_whatsapp_message(from_number, bot_response)

    except Exception as e:
        print(f"Error procesando mensaje entrante: {e}")

    # Meta exige un código HTTP 200 OK para confirmar la recepción
    return Response(content="EVENT_RECEIVED", status_code=200)

# ------------------------------------------------------------------------------
# 4. FUNCIONES AUXILIARES (Gemini & WhatsApp API)
# ------------------------------------------------------------------------------
def generate_gemini_response(prompt_text: str) -> str:
    """ Genera la respuesta utilizando Gemini mediante el SDK google-genai """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
            )
        )
        return response.text
    except Exception as e:
        print(f"Error llamando a la API de Gemini: {e}")
        return "Hola, en este momento estoy teniendo un inconveniente técnico. Por favor escríbenos directamente aquí para atenderte: https://wa.link"


def send_whatsapp_message(to_number: str, text: str):
    """ Envía la respuesta generada al cliente a través de la API Graph de Meta """
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("Faltan las variables WHATSAPP_TOKEN o PHONE_NUMBER_ID en el entorno.")
        return

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }

    try:
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code != 200:
            print(f"Error enviando mensaje a WhatsApp: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Excepción en envío de mensaje a WhatsApp: {e}")
