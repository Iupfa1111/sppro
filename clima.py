import requests

def obtener_clima_caba():
    try:
        # Coordenadas de CABA
        url = "https://api.open-meteo.com/v1/forecast?latitude=-34.6037&longitude=-58.3816&current=temperature_2m,weather_code"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            temp = data["current"]["temperature_2m"]
            code = data["current"]["weather_code"]
            
            # Mapeo simple de códigos WMO del clima a descripciones en español
            condiciones = {
                0: "Despejado ☀️",
                1: "Principalmente despejado 🌤️",
                2: "Parcialmente nublado ⛅",
                3: "Nublado ☁️",
                45: "Neblina 🌫️",
                51: "Llovizna ligera 🌧️",
                61: "Lluvia ligera 🌧️",
                95: "Tormenta ⛈️"
            }
            desc = condiciones.get(code, "Ciclón / Variable 🌤️")
            return f"{temp}°C, {desc}"
        else:
            return "22°C, Parcialmente Nublado (Modo Offline)"
    except Exception:
        return "22°C, Normal (Sin conexión)"
