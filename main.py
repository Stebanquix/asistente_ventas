import os
import sys
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

# 1. Configuración Segura de Credenciales (Render Environment)
API_KEY_SEGURA = os.getenv("GEMINI_API_KEY")
WALINK_ESTABLECIDO = "https://wa.link"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

try:
    print("🔄 Conectando con Google GenAI...")
    client = genai.Client()
    print("✅ Conexión con Gemini establecida con éxito.")
except Exception as e:
    print(f"⚠️ Alerta de inicialización de IA: {str(e)}")

# 2. Inicialización del Servidor FastAPI
app = FastAPI(title="API Oficial de WhatsApp - Pistas Profesionales")

PROMPT_SISTEMA = f"""
Eres el asesor virtual oficial de la plataforma "Pistas Instrumentales Profesionales". 
Tu objetivo es atender de manera profesional y corporativa a los clientes de toda Colombia que se comunican por WhatsApp interesados en adquirir instrumentales de alta fidelidad.
Tarifas: MP3 $20.000 COP / WAV $30.000 COP. Enlace de contacto: {WALINK_ESTABLECIDO}
"""

# --- WEBHOOK PARA LA API OFICIAL DE META ---

@app.get("/webhook", response_class=PlainTextResponse)
def verificar_webhook_meta(request: Request):
    """
    Este es el método GET que Meta necesita de forma obligatoria.
    Responderá de forma inmediata al token 'PistasPro2026'.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode == "subscribe" and token == "PistasPro2026":
        print("✅ Webhook de Meta verificado con éxito.")
        return challenge
        
    return "Servidor de Pistas Activo y Listo para Meta."

@app.post("/webhook")
async def recibir_mensaje_meta(request: Request):
    body = await request.json()
    try:
        if "object" in body and body["object"] == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        message = messages[0]
                        phone_number_id = value.get("metadata", {}).get("phone_number_id")
                        from_number = message.get("from")
                        if message.get("type") == "text":
                            texto_cliente = message.get("text", {}).get("body")
                            
                            # Generación con Gemini
                            response = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=texto_cliente,
                                config=types.GenerateContentConfig(
                                    system_instruction=PROMPT_SISTEMA,
                                    temperature=0.3,
                                )
                            )
                            respuesta_bot = response.text.strip()
                            
                            # Envío de vuelta a Meta
                            url_meta = f"https://facebook.com{phone_number_id}/messages"
                            headers_meta = {
                                "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                                "Content-Type": "application/json"
                            }
                            payload_meta = {
                                "messaging_product": "whatsapp",
                                "to": from_number,
                                "type": "text",
                                "text": {"body": respuesta_bot}
                            }
                            requests.post(url_meta, json=payload_meta, headers=headers_meta)
            return {"status": "success"}
    except Exception as e:
        return {"status": "error", "details": str(e)}
    return {"status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
