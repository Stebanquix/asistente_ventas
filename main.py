import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

# 1. Configuración Segura de Credenciales (Lectura desde el entorno de la nube)
# Render inyectará la clave aquí de forma invisible y privada
API_KEY_SEGURA = os.getenv("GEMINI_API_KEY")
WALINK_ESTABLECIDO = "https://wa.link"

if not API_KEY_SEGURA:
    print("❌ Error crítico: No se detectó la variable GEMINI_API_KEY en el servidor.")
    # No cerramos el proceso con sys.exit para permitir que Render levante el entorno y nos deje configurarla

try:
    print("🔄 Estableciendo conexión con Google GenAI...")
    # El cliente se inicializa automáticamente leyendo la variable GEMINI_API_KEY del entorno
    client = genai.Client()
    print("✅ Conexión con Gemini establecida con éxito.")
except Exception as e:
    print(f"⚠️ Alerta de inicialización (Falta configurar variable en producción): {str(e)}")

# 2. Inicialización del Servidor FastAPI
app = FastAPI(title="API Asistente de Pistas de la Vieja Guardia")

class MensajeEntrada(BaseModel):
    mensaje: str

# El Prompt del Sistema con el tono formal corporativo nacional
PROMPT_SISTEMA = f"""
Eres el asesor virtual oficial del catálogo de Pistas de la Vieja Guardia. 
Tu objetivo es atender de manera profesional y corporativa a los clientes de toda Colombia que se comunican por WhatsApp interesados en adquirir instrumentales.

REGLAS ESTRICTAS DE COMPORTAMIENTO, TONO Y POLÍTICA COMERCIAL:
1. TONO EMPRESARIAL Y NEUTRO: Utilice un lenguaje estrictamente profesional, formal, cortés y comercial. Evite por completo modismos o jergas regionales. Use términos respetuosos como "apreciado cliente", "artista" o diríjase de "usted".
2. GÉNERO INCLUSIVO/UNISEX: Redacte las respuestas de manera neutra, asegurando que el trato sea idéntico para mujeres como para hombres.
3. TARIFAS OFICIALES EN COLOMBIA:
   - Formato MP3 (Calidad estándar de ensayo): $20.000 COP
   - Formato WAV (Máxima fidelidad sin compresión para presentaciones profesionales): $30.000 COP
4. PROMOCIÓN POR VOLUMEN: Si el usuario solicita opciones de descuento, ofrécele el "Pack de 3 pistas en formato MP3" por un valor preferencial de $45.000 COP.
5. POLÍTICA DE REGATEO: Si el cliente insiste de manera relevante en una rebaja, únicamente en ese caso está autorizado a dejar la pista en formato MP3 a $15.000 COP. El formato WAV bajo ninguna circunstancia puede ser rebajado.
6. MÉTODO DE PAGO: Transferencia electrónica directa a las cuentas oficiales de Nequi o Daviplata.
7. CIERRE Y ENLACE DE CONFIRMACIÓN: Suministre siempre el siguiente enlace de contacto oficial: {WALINK_ESTABLECIDO}
"""

@app.post("/webhook")
def recibir_mensaje_whatsapp(datos: MensajeEntrada):
    if not datos.mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
        
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=datos.mensaje,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SISTEMA,
                temperature=0.3,
            )
        )
        return {
            "status": "success",
            "respuesta_bot": response.text.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento de IA: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
