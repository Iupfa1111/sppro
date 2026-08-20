import requests
from datetime import datetime

def obtener_clima():
    """
    Consulta la API meteorológica pública si hay conexión.
    En caso de error o sin red, retorna None para activar la advertencia.
    """
    try:
        url = "https://wttr.in/Buenos+Aires?format=j1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            current = data["current_condition"][0]
            
            temp = f"{current['temp_C']}°C"
            estado = current["weatherDesc"][0]["value"]
            viento = f"{current['windspeedKmph']} km/h"
            humedad = f"{current['humidity']}%"
            presion = f"{current['pressure']} hPa"
            actualizacion = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            return {
                "temperatura": temp,
                "estado": estado,
                "viento": viento,
                "humedad": humedad,
                "presion": presion,
                "actualizacion": actualizacion
            }
    except Exception:
        pass
    return None
