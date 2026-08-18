import datetime
import sqlite3
import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from fpdf import FPDF

st.set_page_config(page_title="SPPRO by Angel Ibañez", layout="wide")

# ==========================================
# 1. GESTIÓN DE BASE DE DATOS (SQLITE + OFFLINE CACHE)
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
        CREATE TABLE IF NOT EXISTS zonas_riesgo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT,
            lat REAL,
            lon REAL,
            radio_km REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache_calles_offline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consulta TEXT UNIQUE,
            lat REAL,
            lon REAL,
            display_name TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("admin", "admin123", 1, "Administrador"))
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("operador1", "user123", 1, "Operador"))
        
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

# ==========================================
# BUSCADOR ESTRUCTURADO DE ALTA PRECISIÓN (GEOLOCALIZACIÓN BLINDADA)
# ==========================================
def buscar_calle_estructurada(calle_input, altura_input, localidad_input):
    if not calle_input or len(calle_input.strip()) < 2:
        return []
    
    calle_limpia = calle_input.strip()
    altura_limpia = altura_input.strip() if altura_input else ""
    
    localidades_dict = {
        "CABA (Ciudad Autónoma de Bs. As.)": "Ciudad Autónoma de Buenos Aires",
        "GBA Zona Norte": "Partido de Vicente López, Buenos Aires",
        "GBA Zona Oeste": "Partido de Morón, Buenos Aires",
        "GBA Zona Sur": "Partido de Avellaneda, Buenos Aires",
        "La Plata y Alrededores": "La Plata, Buenos Aires"
    }
    zona_geo = localidades_dict.get(localidad_input, "Buenos Aires")

    try:
        url = "https://nominatim.openstreetmap.org/search"
        
        if altura_limpia:
            params = {
                "street": f"{altura_limpia} {calle_limpia}",
                "city": zona_geo,
                "format": "json",
                "addressdetails": 1,
                "limit": 5,
                "countrycodes": "ar"
            }
        else:
            query_cruce = calle_limpia.replace(" y ", " esquina ")
            params = {
                "q": f"{query_cruce}, {zona_geo}, Argentina",
                "format": "json",
                "addressdetails": 1,
                "limit": 5,
                "countrycodes": "ar"
            }

        headers = {"User-Agent": "SPPRO_App_AngelIbanez"}
        res = requests.get(url, params=params, headers=headers, timeout=4).json()
        
        opciones = []
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        
        for item in res:
            address = item.get("address", {})
            road = address.get("road", calle_limpia)
            house_num = address.get("house_number", altura_limpia)
            city_name = address.get("city") or address.get("town") or address.get("suburb", zona_geo)
            
            etiqueta = f"{road}"
            if house_num:
                etiqueta += f" {house_num}"
            etiqueta += f" ({city_name})"

            lat_val = float(item["lat"])
            lon_val = float(item["lon"])
            
            opciones.append({"display_name": etiqueta, "lat": lat_val, "lon": lon_val})
            
            # Caché local para modo offline
            cursor.execute("INSERT OR REPLACE INTO cache_calles_offline (consulta, lat, lon, display_name) VALUES (?, ?, ?, ?)",
                           (f"{calle_limpia}{altura_limpia}{localidad_input}".lower(), lat_val, lon_val, etiqueta))
        conn.commit()
        conn.close()
        return opciones
    except:
        # Respaldo SQLite en caso de fallo de red
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        cursor.execute("SELECT display_name, lat, lon FROM cache_calles_offline WHERE consulta LIKE ?", (f"%{calle_limpia.lower()}%",))
        cached = cursor.fetchall()
        conn.close()
        
        if cached:
            return [{"display_name": f"[OFFLINE CACHED] {row[0]}", "lat": row[1], "lon": row[2]} for row in cached]
        return []

def obtener_ruta_terrestre(lat_orig, lon_orig, lat_dest, lon_dest, tipo_ruta="principal"):
    try:
        alternatives = "true" if tipo_ruta in ["plan_b", "plan_c"] else "false"
        url = f"http://router.project-osrm.org/route/v1/driving/{lon_orig},{lat_orig};{lon_dest},{lon_dest}?overview=full&geometries=geojson&steps=true&alternatives={alternatives}"
        res = requests.get(url, timeout=5).json()
        
        if res.get("code") == "Ok":
            routes = res["routes"]
            route_idx = 1 if (tipo_ruta != "principal" and len(routes) > 1) else 0
            route = routes[route_idx]
            
            geometry = route["geometry"]["coordinates"]
            puntos_ruta = [[p[1], p[0]] for p in geometry]
            pasos = []
            for step in route["legs"][0]["steps"]:
                nombre_calle = step.get("name", "").strip()
                distancia = step.get("distance", 0)
                if nombre_calle and distancia > 15:
                    pasos.append(f"Tomar {nombre_calle} ({int(distancia)} m)")
            return puntos_ruta, pasos
    except:
        pass
    return None, []

def verificar_geocercas_ruta(puntos_ruta):
    if not puntos_ruta:
        return []
    
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT descripcion, lat, lon, radio_km FROM zonas_riesgo")
    zonas = cursor.fetchall()
    conn.close()

    alertas_detectadas = set()
    for punto in puntos_ruta:
        p_lat, p_lon = punto[0], punto[1]
        for desc, z_lat, z_lon, radio in zonas:
            distancia_km = ((p_lat - z_lat) * 2 + (p_lon - z_lon) * 2) ** 0.5 * 111
            if distancia_km <= radio:
                alertas_detectadas.add(desc)
                
    return list(alertas_detectadas)

def generar_pdf_hoja_ruta(origen, destino, plan, tiempo, pasos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="SPPRO - HOJA DE RUTA TÁCTICA OPERATIVA", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt=f"Fecha de emisión: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.cell(200, 6, txt="Sistema de Seguridad Patrimonial by Angel Ibañez", ln=True, align="C")
    pdf.line(10, 30, 200, 30)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="1. Detalles del Operativo", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt=f"- Origen: {origen}", ln=True)
    pdf.cell(200, 6, txt=f"- Destino: {destino}", ln=True)
    pdf.cell(200, 6, txt=f"- Plan Aplicado: {plan}", ln=True)
    pdf.cell(200, 6, txt=f"- Tiempo Estimado: {tiempo}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="2. Indicaciones de Trayecto", ln=True)
    pdf.set_font("Arial", "", 9)
    
    for paso in pasos:
        limpio = paso.replace("*", "")
        pdf.cell(200, 6, txt=f"  {limpio}", ln=True)
        
    pdf.ln(15)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 6, txt="Firma Operador a Cargo: ________", ln=True)
    
    return pdf.output(dest="S").encode("latin1")

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
            cursor.execute("SELECT password, activo, rol FROM usuarios WHERE username = ?", (usuario_ingresado,))
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
st.caption(f"by Angel Ibañez | Operador activo: {st.session_state['username']} ({st.session_state['user_role']})")

st.sidebar.title("Menú SPPRO")
opciones = ["🗺️ Planificación de Rutas", "🏢 Entradas/Salidas de Edificios", "🚨 Zonas de Riesgo"]
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
    st.header("🗺️ Navegación, Geocercas y Rúteo Táctico")
    
    loc = get_geolocation()
    lat_gps, lon_gps = -34.6037, -58.3816
    if loc and "coords" in loc:
        lat_gps = loc["coords"]["latitude"]
        lon_gps = loc["coords"]["longitude"]

    col_orig, col_dest = st.columns(2)

    with col_orig:
        st.markdown("### 1. Origen")
        loc_origen = st.selectbox("Jurisdicción Origen:", [
            "CABA (Ciudad Autónoma de Bs. As.)", 
            "GBA Zona Norte", 
            "GBA Zona Oeste", 
            "GBA Zona Sur", 
            "La Plata y Alrededores"
        ], key="loc_o")
        
        c_orig = st.text_input("Calle o Intersección (Ej: Corrientes o Callao y Corrientes)", key="c_o")
        h_orig = st.text_input("Altura / Número (Opcional, ej: 1500)", key="h_o")
        
        sug_origen = buscar_calle_estructurada(c_orig, h_orig, loc_origen)
        coords_orig = None

        if sug_origen:
            op_o = {item["display_name"]: (item["lat"], item["lon"]) for item in sug_origen}
            sel_o = st.selectbox("Confirmar Dirección Exacta (Origen):", list(op_o.keys()), key="box_o")
            coords_orig = op_o[sel_o]
        elif c_orig.strip():
            st.warning("⚠️ Sin resultados automáticos. Verifique los datos o se usará GPS.")
            coords_orig = (lat_gps, lon_gps)
        else:
            coords_orig = (lat_gps, lon_gps)

    with col_dest:
        st.markdown("### 2. Destino")
        loc_destino = st.selectbox("Jurisdicción Destino:", [
            "CABA (Ciudad Autónoma de Bs. As.)", 
            "GBA Zona Norte", 
            "GBA Zona Oeste", 
            "GBA Zona Sur", 
            "La Plata y Alrededores"
        ], key="loc_d")
        
        c_dest = st.text_input("Calle o Intersección Destino", key="c_d")
        h_dest = st.text_input("Altura / Número Destino (Opcional)", key="h_d")
        
        sug_destino = buscar_calle_estructurada(c_dest, h_dest, loc_destino)
        coords_dest = None

        if sug_destino:
            op_d = {item["display_name"]: (item["lat"], item["lon"]) for item in sug_destino}
            sel_d = st.selectbox("Confirmar Dirección Exacta (Destino):", list(op_d.keys()), key="box_d")
            coords_dest = op_d[sel_d]
        elif c_dest.strip():
            st.warning("⚠️ Sin resultados exactos para el destino.")

    st.divider()

    if coords_orig and coords_dest:
        tiempo_est = st.number_input("Tiempo estimado de traslado (minutos)", min_value=1, value=15)
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("🔵 PLAN A (Principal)", use_container_width=True):
                st.session_state["plan_activo"] = "Plan A"
        with col_b2:
            if st.button("🟠 PLAN B (Choque)", use_container_width=True):
                st.session_state["plan_activo"] = "Plan B"
        with col_b3:
            if st.button("🔴 PLAN C (Corte)", use_container_width=True):
                st.session_state["plan_activo"] = "Plan C"

        st.info(f"📌 Plan visualizado: {st.session_state['plan_activo']}")

        plan = st.session_state["plan_activo"]
        tipo = "principal" if plan == "Plan A" else ("plan_b" if plan == "Plan B" else "plan_c")
        puntos_terrestres, pasos_calles = obtener_ruta_terrestre(coords_orig[0], coords_orig[1], coords_dest[0], coords_dest[1], tipo_ruta=tipo)

        alertas_geocercas = verificar_geocercas_ruta(puntos_terrestres)
        if alertas_geocercas:
            st.error(f"🚨 *ALERTA CRÍTICA DE GEOCERCA:* ¡El trayecto seleccionado interseca zonas de riesgo activas! ({', '.join(alertas_geocercas)})")

        centro_mapa = [(coords_orig[0] + coords_dest[0]) / 2, (coords_orig[1] + coords_dest[1]) / 2]
        m = folium.Map(location=centro_mapa, zoom_start=14)
        
        folium.Marker(coords_orig, popup="Origen", icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(coords_dest, popup="Destino", icon=folium.Icon(color="red", icon="flag")).add_to(m)

        if puntos_terrestres:
            color_linea = "blue" if plan == "Plan A" else ("orange" if plan == "Plan B" else "red")
            folium.PolyLine(puntos_terrestres, color=color_linea, weight=6, opacity=0.85).add_to(m)

        st_folium(m, width=1100, height=450)

        st.divider()
        col_pdf1, col_pdf2 = st.columns(2)
        with col_pdf1:
            st.subheader("🛣️ Hoja de Ruta Táctica")
            if pasos_calles:
                for p in pasos_calles:
                    st.markdown(f"• {p}")
            else:
                st.caption("Aconsejado transitar por vías principales.")
                
        with col_pdf2:
            st.subheader("📥 Exportación de Reporte")
            if st.button("Generar Hoja de Ruta en PDF", use_container_width=True):
                pdf_bytes = generar_pdf_hoja_ruta(
                    c_orig if c_orig else "GPS Actual",
                    c_dest,
                    plan,
                    f"{tiempo_est} min",
                    pasos_calles
                )
                st.download_button(
                    label="⬇️ Descargar PDF Oficial",
                    data=pdf_bytes,
                    file_name=f"Hoja_de_Ruta_{plan}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# ==========================================
# SECCIÓN 2: EDIFICIOS
# ==========================================
elif seccion == "🏢 Entradas/Salidas de Edificios":
    st.header("🏢 Registro e Inspección de Edificios Privados")
    es_admin = st.session_state["user_role"] == "Administrador"

    with st.form("form_edificio"):
        nombre_edf = st.text_input("Nombre del Edificio")
        direccion_edf = st.text_input("Dirección")
        desc_accesos = st.text_area("Accesos y Salidas")
        es_privado = st.checkbox("🔒 Privado (Solo Administrador)")
        
        if st.form_submit_button("Guardar Edificio"):
            if nombre_edf and direccion_edf:
                conn = sqlite3.connect("sppro.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO edificios (nombre, direccion, descripcion, adjunto, privado) VALUES (?, ?, ?, ?, ?)",
                               (nombre_edf, direccion_edf, desc_accesos, "Sin adjunto", 1 if es_privado else 0))
                conn.commit()
                conn.close()
                st.success("✅ Edificio guardado con éxito.")
                st.rerun()

    st.divider()
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    if es_admin:
        cursor.execute("SELECT id, nombre, direccion, descripcion, privado FROM edificios")
    else:
        cursor.execute("SELECT id, nombre, direccion, descripcion, privado FROM edificios WHERE privado = 0")
    for edf_id, nombre, direccion, descripcion, privado in cursor.fetchall():
        st.write(f"🏢 *{nombre}* - {direccion} ({'Privado' if privado else 'Público'})")
        st.caption(f"Accesos: {descripcion}")
    conn.close()

# ==========================================
# SECCIÓN 3: ZONAS DE RIESGO
# ==========================================
elif seccion == "🚨 Zonas de Riesgo":
    st.header("🚨 Gestión de Zonas de Riesgo y Geocercas")
    es_admin = st.session_state["user_role"] == "Administrador"

    if es_admin:
        with st.form("form_zona"):
            desc_zona = st.text_input("Motivo de la Zona de Riesgo (ej: Zona Roja / Corte)")
            lat_z = st.number_input("Latitud", value=-34.6037, format="%.4f")
            lon_z = st.number_input("Longitud", value=-58.3816, format="%.4f")
            radio_z = st.number_input("Radio de Afectación (km)", value=0.5, format="%.1f")
            
            if st.form_submit_button("Registrar Geocerca"):
                conn = sqlite3.connect("sppro.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO zonas_riesgo (descripcion, lat, lon, radio_km) VALUES (?, ?, ?, ?)", (desc_zona, lat_z, lon_z, radio_z))
                conn.commit()
                conn.close()
                st.success("✅ Geocerca registrada.")
                st.rerun()

    st.divider()
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, descripcion, lat, lon, radio_km FROM zonas_riesgo")
    for z_id, desc, lat, lon, radio in cursor.fetchall():
        st.warning(f"⚠️ *{desc}* [Lat: {lat}, Lon: {lon}] Radio: {radio} km")
    conn.close()

# ==========================================
# SECCIÓN 4: GESTIÓN DE USUARIOS
# ==========================================
elif seccion == "👥 Gestión de Usuarios":
    st.header("👥 Panel de Usuarios")
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, activo, rol FROM usuarios")
    for u, activo, rol in cursor.fetchall():
        st.write(f"Usuario: {u} | Rol: {rol} | Estado: {'Activo' if activo else 'Inactivo'}")
    conn.close()
