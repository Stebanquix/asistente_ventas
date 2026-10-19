import os
import sys
import requests
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from google import genai
from google.genai import types

# 1. Configuración de Credenciales desde el entorno de Render
API_KEY_SEGURA = os.getenv("GEMINI_API_KEY")
WALINK_ESTABLECIDO = "https://wa.link"
# Token que usted inventará en Meta (Ejemplo: "PistasPro2026")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "PistasPro2026")
# Token de acceso permanente que le dará Meta para enviar mensajes
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

try:
    print("🔄 Conectando con los servicios de Google GenAI...")
    client = genai.Client()
    print("✅ Conexión con Gemini establecida con éxito.")
except Exception as e:
    print(f"⚠️ Alerta de inicialización de IA: {str(e)}")

# 2. Inicialización del Servidor FastAPI
app = FastAPI(title="API Oficial de WhatsApp - Pistas Profesionales")

# Prompt del Sistema Corporativo Nacional
PROMPT_SISTEMA = f"""
Eres el asesor virtual oficial de la plataforma "Pistas Instrumentales Profesionales" (Studio Backing Tracks). 
Tu objetivo es atender de manera profesional y corporativa a los clientes de toda Colombia que se comunican por WhatsApp interesados en adquirir instrumentales de alta fidelidad para cualquier género musical.

REGLAS ESTRICTAS DE COMPORTAMIENTO:
1. TONO EMPRESARIAL Y NEUTRO: Utilice un lenguaje profesional, formal y cortés. Evite por completo jergas regionales. Diríjase al usuario como "artista", "cliente" o de "usted".
2. MULTI-GÉNERO: Confirme que procesa cualquier estilo bajo el estándar "Official Backing Track". Si el tema es inconseguible, ofrezca agendarlo como "Pedido Personalizado de Estudio".
3. TARIFAS: Formato MP3 $20.000 COP / Formato WAV $30.000 COP.
4. COMBOS: Ofrécele el "Combo Pro de Lanzamiento: Pack de 3 pistas en MP3" por $45.000 COP si manifiesta dudas.
5. REGATEO: Si insiste demasiado, puede dejar el MP3 a $15.000 COP como apoyo al artista independiente. El WAV no se rebaja.
6. PAGO: Transferencia a Nequi o Daviplata. Al enviar el comprobante, se libera su descarga de Google Drive.
7. CIERRE: Concluya siempre entregando el siguiente enlace de contacto oficial: {WALINK_ESTABLECIDO}
"""

# --- WEBHOOK PARA LA API OFICIAL DE META ---

@app.get("/webhook")
def verificar_webhook_meta(request: Request):
    """
    Este endpoint es de uso exclusivo para que Meta valide que su servidor
    es seguro y real cuando lo configure en el panel de desarrolladores.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            print("✅ Webhook de Meta verificado y enlazado correctamente.")
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Token de verificación inválido")
    return "Servidor activo esperando validación de Meta."

@app.post("/webhook")
async def recibir_mensaje_meta(request: Request):
    """
    Este endpoint recibe las notificaciones en tiempo real de Meta, procesa
    el texto con Gemini y responde al cliente directamente a su celular.
    """
    body = await request.json()
    
    try:
        # Validamos que sea un mensaje de texto válido enviado por un usuario
        if "object" in body and body["object"] == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    if messages:
                        message = messages[0]
                        phone_number_id = value.get("metadata", {}).get("phone_number_id")
                        from_number = message.get("from") # Teléfono del cliente
                        
                        # Filtramos estrictamente mensajes de texto limpio
                        if message.get("type") == "text":
                            texto_cliente = message.get("text", {}).get("body")
                            
                            # Llamamos a la Inteligencia Artificial de Gemini
                            response = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=texto_cliente,
                                config=types.GenerateContentConfig(
                                    system_instruction=PROMPT_SISTEMA,
                                    temperature=0.3,
                                )
                            )
                            respuesta_bot = response.text.strip()
                            
                            # Enviamos la respuesta de vuelta usando la API Oficial de Meta
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
                            
                            # Despachamos el mensaje a internet de forma nativa
                            requests.post(url_meta, json=payload_meta, headers=headers_meta)
                            
            return {"status": "success"}
    except Exception as e:
        print(f"❌ Error al procesar datos de Meta: {str(e)}")
        return {"status": "error", "details": str(e)}
        
    return {"status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
