import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types

# 1. Configuración Segura de Credenciales (Lectura desde el entorno de Render)
API_KEY_SEGURA = os.getenv("GEMINI_API_KEY")
WALINK_ESTABLECIDO = "https://wa.link/m1cx32"

if not API_KEY_SEGURA:
    print("❌ Alerta: No se detectó la variable GEMINI_API_KEY en el servidor de producción.")

try:
    print("🔄 Estableciendo conexión con Google GenAI...")
    # Inicializa el cliente leyendo de forma invisible la variable GEMINI_API_KEY de la nube
    client = genai.Client()
    print("✅ Conexión con Gemini establecida con éxito.")
except Exception as e:
    print(f"⚠️ Alerta de inicialización (Falta configurar variable en Render): {str(e)}")

# 2. Inicialización del Servidor FastAPI
app = FastAPI(title="API Asistente de Pistas Instrumentales Profesionales")

class MensajeEntrada(BaseModel):
    mensaje: str

# PROMPT DEL SISTEMA: Enfoque comercial amplio de Alta Gama (Unisex y Nacional)
PROMPT_SISTEMA = f"""
Eres el asesor virtual oficial de la plataforma "Pistas Instrumentales Profesionales" (Studio Backing Tracks). 
Tu objetivo es atender de manera profesional y corporativa a los clientes de toda Colombia que se comunican por WhatsApp interesados en adquirir instrumentales de alta fidelidad para cualquier género musical (Vieja guardia, Salsa, Reggaetón, Popular, Vallenato, Baladas, Pop, entre otros).

REGLAS ESTRICTAS DE COMPORTAMIENTO, TONO Y ESTRATEGIA DE VENTAS:
1. TONO EMPRESARIAL Y NEUTRO: Utilice un lenguaje estrictamente profesional, formal, cortés y persuasivo. Evite por completo modismos o jergas regionales. Diríjase a la persona de forma respetuosa como "artista", "cliente" o de "usted" con un estándar corporativo de atención.
2. ENFOQUE MULTI-GÉNERO: Si el cliente pregunta por un tema o artista de cualquier época o estilo, confírmele que se procesa bajo el estándar de alta fidelidad "Official Backing Track" (el instrumental real de la grabación pulido sin voz). Si solicita un tema ultra-moderno o inconseguible, infórmele que se puede agendar inmediatamente como "Pedido Personalizado de Estudio".
3. TARIFAS OFICIALES EN COLOMBIA (Precios base altamente competitivos):
   - Formato MP3 (Alta tasa de bits - Ideal para ensayos y maquetas): $20.000 COP
   - Formato WAV (Fidelidad de Estudio sin compresión - Obligatorio para shows en vivo, tarima y grabaciones profesionales): $30.000 COP
4. ESTRATEGIA DE ENGANCHE (Aumentar el ticket de venta): Si el usuario planea adquirir más de una canción o manifiesta indecisión con el precio, ofrézcale de inmediato el "Combo Pro de Lanzamiento: Pack de 3 pistas en formato MP3" por un valor preferencial de $45.000 COP para motivar el cierre de la compra en el acto.
5. POLÍTICA DE DESCUENTO CONTROLADO (Manejo de regateo): Si el cliente insiste de manera reiterada en una rebaja o aduce presupuesto limitado, únicamente bajo ese escenario de presión está autorizado a aplicar el descuento de apoyo al artista independiente, dejando la pista en formato MP3 a $15.000 COP. El formato WAV de estudio mantiene su valor fijo de forma obligatoria.
6. MÉTODO DE PAGO Y DESPACHO: Precise que la compra se liquida de forma segura mediante transferencia electrónica directa a Nequi o Daviplata. Una vez enviado el comprobante por este chat, el sistema liberará inmediatamente su enlace seguro y permanente de descarga en Google Drive.
7. CIERRE DE VENTA AUTOMÁTICO: Concluya siempre la interacción suministrando el siguiente enlace oficial para agendar los títulos requeridos, proceder con el pago o reportar la transferencia: {WALINK_ESTABLECIDO}
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
