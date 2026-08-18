import datetime
import sqlite3
import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="SPPRO by Angel Ibañez", layout="wide")

# ==========================================
# GESTIÓN DE BASE DE DATOS (SQLITE)
# ==========================================


def init_db():
  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            activo INTEGER NOT NULL,
            rol TEXT NOT NULL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS edificios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT NOT NULL,
            descripcion TEXT,
            adjunto TEXT,
            privado INTEGER NOT NULL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_rutas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            origen TEXT,
            destino TEXT,
            tiempo TEXT,
            clima TEXT,
            plan TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS rutas_frecuentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_ruta TEXT,
            origen TEXT,
            destino TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS zonas_riesgo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT,
            lat REAL,
            lon REAL,
            radio_km REAL
        )
    """)

  cursor.execute("SELECT COUNT(*) FROM usuarios")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO usuarios VALUES (?, ?, ?, ?)",
        ("admin", "admin123", 1, "Administrador"),
    )
    cursor.execute(
        "INSERT INTO usuarios VALUES (?, ?, ?, ?)",
        ("operador1", "user123", 1, "Operador"),
    )

  cursor.execute("SELECT COUNT(*) FROM edificios")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO edificios (nombre, direccion, descripcion, adjunto,"
        " privado) VALUES (?, ?, ?, ?, ?)",
        (
            "Edificio Central / Planta",
            "Av. Corrientes 1000, CABA",
            (
                "Entrada principal sobre avenida, salida de emergencia por"
                " calle lateral."
            ),
            "Sin adjunto",
            0,
        ),
    )

  conn.commit()
  conn.close()


init_db()

# ==========================================
# ESTADOS DE SESIÓN Y CONFIGURACIÓN
# ==========================================
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
  st.session_state["user_role"] = None
  st.session_state["username"] = None

if "plan_activo" not in st.session_state:
  st.session_state["plan_activo"] = "Plan A"

WMO_CODES = {
    0: "☀️ Despejado / Soleado",
    1: "🌤️ Mayormente despejado",
    2: "⛅ Parcialmente nublado",
    3: "☁️ Cubierto / Nublado",
    45: "🌫️ Niebla",
    51: "🌧️ Llovizna ligera",
    61: "🌧️ Lluvia ligera",
    63: "🌧️ Lluvia moderada",
    65: "🌧️ Lluvia fuerte",
    95: "🌩️ Tormenta eléctrica",
}


# ==========================================
# FUNCIONES AUXILIARES (APIS Y DB)
# ==========================================
def buscar_direcciones_similares(query):
  if not query or len(query.strip()) < 3:
    return []

  query_limpio = query.lower().strip()
  if " y " in query_limpio:
    query_procesado = query_limpio.replace(" y ", ", ")
  else:
    query_procesado = query_limpio

  if (
      "buenos aires" not in query_procesado
      and "caba" not in query_procesado
      and "argentina" not in query_procesado
  ):
    query_procesado = f"{query_procesado}, Buenos Aires, Argentina"

  try:
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query_procesado,
        "format": "json",
        "addressdetails": 1,
        "limit": 6,
        "countrycodes": "ar",
    }
    headers = {"User-Agent": "SPPRO_App_AngelIbanez"}
    res = requests.get(url, params=params, headers=headers, timeout=5).json()

    opciones = []
    for item in res:
      direccion_formateada = item.get("display_name", "Ubicación desconocida")
      address = item.get("address", {})
      calle = address.get("road", "")
      numero = address.get("house_number", "")
      barrio_o_ciudad = (
          address.get("city")
          or address.get("town")
          or address.get("suburb")
          or address.get("county", "")
      )

      etiqueta_visual = f"{calle}"
      if numero:
        etiqueta_visual += f" {numero}"
      if barrio_o_ciudad:
        etiqueta_visual += f" ({barrio_o_ciudad})"
      else:
        etiqueta_visual += f" - {direccion_formateada}"

      opciones.append({
          "display_name": etiqueta_visual,
          "lat": float(item["lat"]),
          "lon": float(item["lon"]),
      })
    return opciones
  except:
    return []


def obtener_direccion_inversa(lat, lon):
  """Geocodificación inversa: Convierte coordenadas de un clic en dirección legible."""
  try:
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": 1}
    headers = {"User-Agent": "SPPRO_App_AngelIbanez"}
    res = requests.get(url, params=params, headers=headers, timeout=5).json()
    if "display_name" in res:
      address = res.get("address", {})
      calle = address.get("road", "")
      numero = address.get("house_number", "")
      ciudad = (
          address.get("city")
          or address.get("town")
          or address.get("suburb")
          or ""
      )
      base = f"{calle} {numero}".strip()
      if ciudad:
        base += f" ({ciudad})"
      return base if base else res["display_name"]
  except:
    pass
  return f"Lat: {lat:.4f}, Lon: {lon:.4f}"


def obtener_ruta_terrestre(
    lat_orig, lon_orig, lat_dest, lon_dest, tipo_ruta="principal"
):
  """Calcula rutas reales y dinámicas mediante OSRM (Incluye alternativas)."""
  try:
    # Si es alternativa, forzamos parámetros de desvío (waypoints desplazados o rutas alternativas de OSRM)
    alternatives = "true" if tipo_ruta in ["plan_b", "plan_c"] else "false"
    url = f"http://router.project-osrm.org/route/v1/driving/{lon_orig},{lat_orig};{lon_dest},{lat_dest}?overview=full&geometries=geojson&steps=true&alternatives={alternatives}"
    res = requests.get(url, timeout=6).json()

    if res.get("code") == "Ok":
      routes = res["routes"]
      # Seleccionamos la ruta principal (índice 0) o la alternativa (índice 1 si existe)
      route_idx = 1 if (tipo_ruta != "principal" and len(routes) > 1) else 0
      route = routes[route_idx]

      geometry = route["geometry"]["coordinates"]
      puntos_ruta = [[p[1], p[0]] for p in geometry]
      pasos = []
      for step in route["legs"][0]["steps"]:
        nombre_calle = step.get("name", "").strip()
        distancia = step.get("distance", 0)
        if nombre_calle and distancia > 20:
          pasos.append(f"Tomar {nombre_calle} ({int(distancia)} m)")
      return puntos_ruta, pasos
  except:
    pass
  return None, []


def obtener_clima_detallado(lat, lon):
  try:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    res = requests.get(url, timeout=5).json()
    if "current_weather" in res:
      cw = res["current_weather"]
      temp = cw.get("temperature", "N/D")
      viento = cw.get("windspeed", "N/D")
      code = cw.get("weathercode", 0)
      condicion = WMO_CODES.get(code, "🌤️ Condición estable")
      return (
          f"Condición: {condicion} | 🌡️ Temp: {temp}°C | 💨 Viento:"
          f" {viento} km/h",
          condicion,
      )
  except:
    pass
  return "Información meteorológica no disponible.", "No disponible"


def verificar_zonas_riesgo(lat, lon):
  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()
  cursor.execute("SELECT descripcion, lat, lon, radio_km FROM zonas_riesgo")
  zonas = cursor.fetchall()
  conn.close()

  alertas = []
  for desc, z_lat, z_lon, radio in zonas:
    distancia_aprox = (
        (lat - z_lat) * 2 + (lon - z_lon) * 2
    ) ** 0.5 * 111
    if distancia_aprox <= radio:
      alertas.append(desc)
  return alertas


# ==========================================
# CONTROL DE ACCESO (LOGIN)
# ==========================================
if not st.session_state["logged_in"]:
  st.title("SPPRO")
  st.caption("by Angel Ibañez - Seguridad Patrimonial")
  st.divider()

  _, col_login, _ = st.columns([1, 2, 1])
  with col_login:
    st.subheader("Acceso al Sistema")
    usuario_ingresado = st.text_input("Usuario")
    clave_ingresada = st.text_input("Contraseña", type="password")

    if st.button("Ingresar", use_container_width=True):
      conn = sqlite3.connect("sppro.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT password, activo, rol FROM usuarios WHERE username = ?",
          (usuario_ingresado,),
      )
      res = cursor.fetchone()
      conn.close()

      if res and res[0] == clave_ingresada:
        if res[1] == 1:
          st.session_state["logged_in"] = True
          st.session_state["username"] = usuario_ingresado
          st.session_state["user_role"] = res[2]
          st.rerun()
        else:
          st.error("⚠️ Usuario desactivado por el administrador.")
      else:
        st.error("❌ Usuario o contraseña incorrectos.")
  st.stop()

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("SPPRO")
st.caption(
    f"by Angel Ibañez | Operador activo: {st.session_state['username']}"
    f" ({st.session_state['user_role']})"
)

st.sidebar.title("Menú SPPRO")
opciones = [
    "🗺️ Planificación de Rutas",
    "🏢 Entradas/Salidas de Edificios",
    "🚨 Zonas de Riesgo",
]
if st.session_state["user_role"] == "Administrador":
  opciones.append("👥 Gestión de Usuarios")

seccion = st.sidebar.radio("Navegación:", opciones)

if st.sidebar.button("Cerrar Sesión", use_container_width=True):
  st.session_state["logged_in"] = False
  st.rerun()

# ==========================================
# SECCIÓN 1: PLANIFICACIÓN DE RUTAS
# ==========================================
if seccion == "🗺️ Planificación de Rutas":
  st.header("🗺️ Navegación y Rúteo de Seguridad Terrestre")

  loc = get_geolocation()
  lat_gps, lon_gps = -34.6037, -58.3816
  if loc and "coords" in loc:
    lat_gps = loc["coords"]["latitude"]
    lon_gps = loc["coords"]["longitude"]

  conn = sqlite3.connect("sppro.db")
  df_frecuentes = pd.read_sql_query(
      "SELECT * FROM rutas_frecuentes", conn
  )
  conn.close()

  if not df_frecuentes.empty:
    with st.expander("⚡ Cargar Ruta Frecuente / Preestablecida"):
      sel_frec = st.selectbox(
          "Seleccioná un circuito frecuente:", df_frecuentes["nombre_ruta"]
      )
      if st.button("Aplicar Ruta Frecuente"):
        fila = df_frecuentes[
            df_frecuentes["nombre_ruta"] == sel_frec
        ].iloc[0]
        st.session_state["input_origen_val"] = fila["origen"]
        st.session_state["input_destino_val"] = fila["destino"]
        st.rerun()

  # Sección de interacción por clic en el mapa (Geocodificación Inversa)
  if "clicked_lat" not in st.session_state:
    st.session_state["clicked_lat"] = None
    st.session_state["clicked_lon"] = None

  col_orig, col_dest = st.columns(2)

  orig_default = st.session_state.get("input_origen_val", "")
  dest_default = st.session_state.get("input_destino_val", "")

  with col_orig:
    txt_origen = st.text_input(
        "1. Origen (Altura, Calle X y Calle Y, o Lugar):",
        value=orig_default,
        placeholder="Ej: Corrientes 1500 o Callao y Corrientes",
    )
    sug_origen = buscar_direcciones_similares(txt_origen)
    coords_orig = None

    if sug_origen:
      opciones_orig_dict = {
          item["display_name"]: (item["lat"], item["lon"]) for item in sug_origen
      }
      sel_orig = st.selectbox(
          "Coincidencia exacta (Origen):",
          list(opciones_orig_dict.keys()),
          key="sel_o",
      )
      coords_orig = opciones_orig_dict[sel_orig]
    elif txt_origen.strip():
      st.warning(
          "⚠️ Ingresá una dirección o intersección válida para ubicar el"
          " origen."
      )
    else:
      coords_orig = (lat_gps, lon_gps)

  with col_dest:
    txt_destino = st.text_input(
        "2. Destino (Altura, Calle X y Calle Y, o Lugar):",
        value=dest_default,
        placeholder="Ej: Plaza de Mayo, CABA",
    )
    sug_destino = buscar_direcciones_similares(txt_destino)
    coords_dest = None

    if sug_destino:
      opciones_dest_dict = {
          item["display_name"]: (item["lat"], item["lon"]) for item in sug_destino
      }
      sel_dest = st.selectbox(
          "Coincidencia exacta (Destino):",
          list(opciones_dest_dict.keys()),
          key="sel_d",
      )
      coords_dest = opciones_dest_dict[sel_dest]
    elif txt_destino.strip():
      st.warning(
          "⚠️ Ingresá una dirección o intersección válida para ubicar el"
          " destino."
      )

  # Panel auxiliar si se hizo clic en el mapa
  if st.session_state["clicked_lat"] and st.session_state["clicked_lon"]:
    lat_c = st.session_state["clicked_lat"]
    lon_c = st.session_state["clicked_lon"]
    dir_inversa = obtener_direccion_inversa(lat_c, lon_c)
    st.info(
        f"📍 *Punto seleccionado en el mapa:* {dir_inversa} (Lat: {lat_c:.4f},"
        " Lon: {lon_c:.4f})"
    )
    col_ic1, col_ic2 = st.columns(2)
    with col_ic1:
      if st.button("Usar como Origen"):
        st.session_state["input_origen_val"] = dir_inversa
        st.rerun()
    with col_ic2:
      if st.button("Usar como Destino"):
        st.session_state["input_destino_val"] = dir_inversa
        st.rerun()

  st.divider()

  if coords_orig and coords_dest:
    alertas_origen = verificar_zonas_riesgo(coords_orig[0], coords_orig[1])
    alertas_destino = verificar_zonas_riesgo(coords_dest[0], coords_dest[1])
    if alertas_origen or alertas_destino:
      st.error(
          "🚨 *ALERTA DE SEGURIDAD:* ¡El origen o destino se encuentra dentro"
          f" de una zona de riesgo o corte activo! ({', '.join(alertas_origen + alertas_destino)})"
      )

    tiempo_est = st.number_input(
        "Tiempo estimado de traslado (minutos)", min_value=1, value=15
    )

    st.subheader("📍 Visualización de Trazado y Planes de Emergencia")

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
      if st.button("🔵 Ver PLAN A (Ruta Principal)", use_container_width=True):
        st.session_state["plan_activo"] = "Plan A"
    with col_b2:
      if st.button("🟠 Ver PLAN B (Desvío Choque)", use_container_width=True):
        st.session_state["plan_activo"] = "Plan B"
    with col_b3:
      if st.button("🔴 Ver PLAN C (Desvío Corte)", use_container_width=True):
        st.session_state["plan_activo"] = "Plan C"

    st.info(
        f"📌 Plan visualizado actualmente: {st.session_state['plan_activo']}"
    )

    texto_clima, estado_clima = obtener_clima_detallado(
        coords_orig[0], coords_orig[1]
    )
    st.info(f"🌤️ Estado del Clima: {texto_clima}")

    col_acc1, col_acc2 = st.columns(2)
    with col_acc1:
      if st.button("💾 Guardar Recorrido en Historial"):
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO historial_rutas (fecha, origen, destino, tiempo,"
            " clima, plan) VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                txt_origen if txt_origen else "Ubicación GPS",
                txt_destino,
                f"{tiempo_est} min",
                estado_clima,
                st.session_state["plan_activo"],
            ),
        )
        conn.commit()
        conn.close()
        st.success("✅ Recorrido guardado con éxito en la base de datos.")

    with col_acc2:
      with st.popover("⭐ Guardar como Ruta Frecuente"):
        nombre_frec = st.text_input("Nombre descriptivo (ej: Base -> Planta)")
        if st.button("Confirmar Guardado"):
          if nombre_frec and txt_origen and txt_destino:
            conn = sqlite3.connect("sppro.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO rutas_frecuentes (nombre_ruta, origen, destino)"
                " VALUES (?, ?, ?)",
                (nombre_frec, txt_origen, txt_destino),
            )
            conn.commit()
            conn.close()
            st.success("✅ Ruta frecuente guardada.")

    # Selección dinámica del tipo de ruta según el plan activo
    plan = st.session_state["plan_activo"]
    if plan == "Plan A":
      puntos_terrestres, pasos_calles = obtener_ruta_terrestre(
          coords_orig[0],
          coords_orig[1],
          coords_dest[0],
          coords_dest[1],
          tipo_ruta="principal",
      )
    elif plan == "Plan B":
      puntos_terrestres, pasos_calles = obtener_ruta_terrestre(
          coords_orig[0],
          coords_orig[1],
          coords_dest[0],
          coords_dest[1],
          tipo_ruta="plan_b",
      )
    else:  # Plan C
      puntos_terrestres, pasos_calles = obtener_ruta_terrestre(
          coords_orig[0],
          coords_orig[1],
          coords_dest[0],
          coords_dest[1],
          tipo_ruta="plan_c",
      )

    centro_mapa = [
        (coords_orig[0] + coords_dest[0]) / 2,
        (coords_orig[1] + coords_dest[1]) / 2,
    ]
    m = folium.Map(location=centro_mapa, zoom_start=14)

    folium.Marker(
        coords_orig,
        popup="Origen",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)
    folium.Marker(
        coords_dest,
        popup="Destino",
        icon=folium.Icon(color="red", icon="flag"),
    ).add_to(m)

    if plan == "Plan A":
      if puntos_terrestres:
        folium.PolyLine(
            puntos_terrestres,
            color="blue",
            weight=6,
            opacity=0.85,
            popup="Plan A: Ruta Principal",
        ).add_to(m)
    elif plan == "Plan B":
      if puntos_terrestres:
        folium.PolyLine(
            puntos_terrestres,
            color="orange",
            weight=6,
            opacity=0.9,
            popup="Plan B: Ruta Alternativa Real por Choque",
        ).add_to(m)
      st.warning("⚠️ Mostrando Ruta Alternativa Real por Siniestro (Plan B).")
    elif plan == "Plan C":
      if puntos_terrestres:
        folium.PolyLine(
            puntos_terrestres,
            color="red",
            weight=6,
            opacity=0.9,
            popup="Plan C: Ruta Perimetral Alternativa Real por Bloqueo",
        ).add_to(m)
      st.error("🚨 Mostrando Ruta Perimetral Real por Bloqueo (Plan C).")

    # Renderizar mapa interactivo y capturar clics (Geocodificación inversa)
    map_data = st_folium(m, width=1100, height=480)
    if map_data and map_data.get("last_clicked"):
      click_lat = map_data["last_clicked"]["lat"]
      click_lon = map_data["last_clicked"]["lng"]
      if (
          st.session_state["clicked_lat"] != click_lat
          or st.session_state["clicked_lon"] != click_lon
      ):
        st.session_state["clicked_lat"] = click_lat
        st.session_state["clicked_lon"] = click_lon
        st.rerun()

    st.divider()
    st.subheader("🛣️ Hoja de Ruta Terrestre (Trazado Activo)")
    if pasos_calles:
      for p in pasos_calles:
        st.markdown(f"• {p}")
    else:
      st.caption("Transitar por avenidas principales conectoras.")

  st.divider()
  st.subheader("📜 Historial de Rutas Guardadas")
  conn = sqlite3.connect("sppro.db")
  df_historial = pd.read_sql_query(
      "SELECT fecha, origen, destino, tiempo, clima, plan FROM"
      " historial_rutas",
      conn,
  )
  conn.close()

  if not df_historial.empty:
    st.dataframe(df_historial, use_container_width=True)
    csv = df_historial.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar Historial Operativo (CSV)",
        data=csv,
        file_name="historial_operativo_sppro.csv",
        mime="text/csv",
    )
  else:
    st.caption("No hay registros en el historial.")

# ==========================================
# SECCIÓN 2: EDIFICIOS
# ==========================================
elif seccion == "🏢 Entradas/Salidas de Edificios":
  st.header("🏢 Registro e Inspección de Edificios Privados")
  es_admin = st.session_state["user_role"] == "Administrador"

  with st.form("form_edificio"):
    st.subheader("➕ Cargar Nuevo Edificio / Punto de Control")
    nombre_edf = st.text_input("Nombre del Edificio / Planta")
    direccion_edf = st.text_input("Dirección Completa")
    desc_accesos = st.text_area(
        "Descripción de Entradas, Salidas y Puntos de Evacuación"
    )

    foto_subida = st.file_uploader(
        "Adjuntar archivo / plano", type=["jpg", "png", "jpeg", "pdf"]
    )
    es_privado = st.checkbox(
        "🔒 Marcar como exclusivo/privado (Solo Administrador)"
    )

    if st.form_submit_button("Guardar Edificio"):
      if nombre_edf and direccion_edf:
        origen_adjunto = (
            f"Archivo: {foto_subida.name}" if foto_subida else "Sin adjunto"
        )
        priv_val = 1 if es_privado else 0

        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO edificios (nombre, direccion, descripcion, adjunto,"
            " privado) VALUES (?, ?, ?, ?, ?)",
            (
                nombre_edf,
                direccion_edf,
                desc_accesos,
                origen_adjunto,
                priv_val,
            ),
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Edificio '{nombre_edf}' guardado correctamente.")
        st.rerun()
      else:
        st.warning("Ingresá nombre y dirección.")

  st.divider()
  st.subheader("📋 Edificios Registrados")
  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()
  if es_admin:
    cursor.execute(
        "SELECT id, nombre, direccion, descripcion, adjunto, privado FROM"
        " edificios"
    )
  else:
    cursor.execute(
        "SELECT id, nombre, direccion, descripcion, adjunto, privado FROM"
        " edificios WHERE privado = 0"
    )
  lista_edificios = cursor.fetchall()
  conn.close()

  if lista_edificios:
    for (
        edf_id,
        nombre,
        direccion,
        descripcion,
        adjunto,
        privado,
    ) in lista_edificios:
      estado_vis = "🔒 Privado (Admin)" if privado == 1 else "🌐 Público"
      with st.expander(f"🏢 {nombre} - {direccion} | [{estado_vis}]"):
        st.write(f"Accesos y Salidas: {descripcion}")
        st.write(f"Archivo / Foto: {adjunto}")
        if es_admin:
          st.divider()
          if st.button("Cambiar Visibilidad", key=f"cambiar_priv_{edf_id}"):
            nuevo_priv = 0 if privado == 1 else 1
            conn = sqlite3.connect("sppro.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE edificios SET privado = ? WHERE id = ?",
                (nuevo_priv, edf_id),
            )
            conn.commit()
            conn.close()
            st.rerun()
  else:
    st.caption("No hay edificios registrados.")

# ==========================================
# SECCIÓN 3: ZONAS DE RIESGO
# ==========================================
elif seccion == "🚨 Zonas de Riesgo":
  st.header("🚨 Gestión de Zonas de Riesgo y Cortes Activos")
  es_admin = st.session_state["user_role"] == "Administrador"

  if es_admin:
    with st.form("form_zona"):
      st.subheader("➕ Registrar Nueva Alerta / Corte")
      desc_zona = st.text_input(
          "Descripción del Motivo (ej: Corte por manifestación / Zona roja)"
      )
      lat_z = st.number_input("Latitud aproximada", value=-34.6037, format="%.4f")
      lon_z = st.number_input(
          "Longitud aproximada", value=-58.3816, format="%.4f"
      )
      radio_z = st.number_input(
          "Radio de afectación (km)", value=0.5, format="%.1f"
      )

      if st.form_submit_button("Guardar Zona de Riesgo"):
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO zonas_riesgo (descripcion, lat, lon, radio_km) VALUES"
            " (?, ?, ?, ?)",
            (desc_zona, lat_z, lon_z, radio_z),
        )
        conn.commit()
        conn.close()
        st.success("✅ Zona de riesgo registrada correctamente.")
        st.rerun()

  st.divider()
  st.subheader("📋 Zonas Registradas Actuales")
  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, descripcion, lat, lon, radio_km FROM zonas_riesgo")
  zonas = cursor.fetchall()
  conn.close()

  if zonas:
    for z_id, desc, lat, lon, radio in zonas:
      st.warning(f"⚠️ *{desc}* (Lat: {lat}, Lon: {lon}) - Radio: {radio} km")
      if es_admin:
        if st.button("Eliminar Alerta", key=f"del_z_{z_id}"):
          conn = sqlite3.connect("sppro.db")
          cursor = conn.cursor()
          cursor.execute("DELETE FROM zonas_riesgo WHERE id = ?", (z_id,))
          conn.commit()
          conn.close()
          st.rerun()
  else:
    st.info("No hay zonas de riesgo ni cortes activos cargados.")

# ==========================================
# SECCIÓN 4: GESTIÓN DE USUARIOS
# ==========================================
elif seccion == "👥 Gestión de Usuarios":
  st.header("👥 Panel de Administración de Usuarios")

  st.subheader("➕ Crear Nuevo Usuario")
  with st.form("nuevo_usuario"):
    nuevo_user = st.text_input("Nombre de Usuario")
    nueva_pass = st.text_input("Contraseña Inicial", type="password")
    rol = st.selectbox("Rol", ["Operador", "Administrador"])
    if st.form_submit_button("Crear Usuario"):
      if nuevo_user and nueva_pass:
        try:
          conn = sqlite3.connect("sppro.db")
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO usuarios VALUES (?, ?, ?, ?)",
              (nuevo_user, nueva_pass, 1, rol),
          )
          conn.commit()
          conn.close()
          st.success(f"✅ Usuario '{nuevo_user}' creado exitosamente.")
        except:
          st.error("❌ El nombre de usuario ya existe.")

  st.divider()
  st.subheader("⚙️ Control de Estado de Usuarios")
  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()
  cursor.execute("SELECT username, activo, rol FROM usuarios")
  usuarios_db = cursor.fetchall()
  conn.close()

  for u, activo, rol in usuarios_db:
    if u != "admin":
      col_info, col_btn = st.columns([3, 1])
      estado_texto = "🟢 Activo" if activo == 1 else "🔴 Inactivo"
      col_info.write(f"Usuario: {u} | Rol: {rol} | Estado: {estado_texto}")

      nuevo_estado = 0 if activo == 1 else 1
      texto_btn = "Desactivar" if activo == 1 else "Reactivar"

      if col_btn.button(texto_btn, key=f"btn_{u}"):
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET activo = ? WHERE username = ?", (nuevo_estado, u)
        )
        conn.commit()
        conn.close()
        st.rerun()
