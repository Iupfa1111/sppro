# clima.py
import requests

def obtener_clima_caba():
    try:
        # API pública Open-Meteo para CABA en tiempo real (sin necesidad de claves externas)
        url = "https://api.open-meteo.com/v1/forecast?latitude=-34.6037&current=temperature_2m,weather_code&timezone=America/Argentina/Buenos_Aires"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            data = res.json()["current"]
            temp = data["temperature_2m"]
            code = data["weather_code"]
            
            # Interpretación simple del código del clima
            if code == 0: estado = "Despejado ☀️"
            elif code <= 3: estado = "Parcialmente nublado ⛅"
            elif code <= 48: estado = "Neblina o Nublado 🌫️"
            elif code <= 67: estado = "Lluvioso 🌧️"
            else: estado = "Tormenta ⛈️"
            
            return f"{temp}°C, {estado}"
    except Exception:
        pass
    return "Datos climáticos no disponibles"
