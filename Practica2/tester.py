import time
import random
import requests
import json

# --- CONFIGURACIÓN ---
# Cambia esto por la URL de tu API real o tu contenedor Docker

host = "localhost"
port = 4000
endpoint = "detectar"

API_URL = f"http://{host}:{port}/{endpoint}" 

# Probabilidad de anomalía (0.1 = 10% de las veces)
PROBABILIDAD_ANOMALIA = 0.15 

def generar_temperatura():
    """
    Genera una temperatura. 
    Normalmente entre 20 y 25 grados.
    Si hay anomalía, genera un pico extremo (>80 o <0).
    """
    if random.random() < PROBABILIDAD_ANOMALIA:
        # --- CASO ANOMALÍA ---
        # Generamos un pico de calor o frío extremo
        if random.choice([True, False]):
            temp = random.uniform(125.0, 150.0)  # Fuego/Sobrecalentamiento
            tipo = "ANOMALIA_ALTA"
        else:
            temp = random.uniform(-20.0, 0.0)   # Fallo de sensor/Congelación
            tipo = "ANOMALIA_BAJA"
    else:
        # --- CASO NORMAL ---
        # Temperatura ambiente estable con ligera variación
        temp = random.uniform(65.0, 71.0)
        tipo = "NORMAL"
    
    return round(temp, 2), tipo

def main():
    print(f"--- Iniciando simulador de sensor hacia: {API_URL} ---")
    print("Presiona CTRL+C para detener.\n")

    while True:
        temperatura, estado = generar_temperatura()
        
        payload = {
            "sensor_id": "sensor_01",
            "timestamp": time.time(),
            "value": temperatura,
            "status": estado
        }

        try:
            # Enviamos los datos a la API
            response = requests.get(API_URL + "?" + f"dato={temperatura}", timeout=2)
            
            # Imprimimos en consola para que veas qué está pasando
            texto_resp = response.json()
            deteccion = texto_resp[0]['anomalia']
            
            msg = f"Enviado: {temperatura}°F [{estado}] -> Respuesta: {response.status_code} Deteccion: {deteccion}"
            if estado != "NORMAL":
                print(f"⚠️  {msg}", 'Anomalia:', '✅' if deteccion == 'si' else '❌') # Destacamos la anomalía visualmente
            else:
                print(f"✅ {msg}", 'Anomalia:', '✅' if deteccion == 'no' else '❌')
        except requests.exceptions.ConnectionError:
            print(f"❌ Error: No se pudo conectar a {API_URL}. ¿Está levantado el Docker?")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
    
        time.sleep(1)

        # Esperar 1 segundo

if __name__ == "__main__":
    main()