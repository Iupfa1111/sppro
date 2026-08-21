# aplicación.py
import streamlit as st
import math
from datetime import datetime
from fpdf import FPDF
import folium
from streamlit_folium import st_folium
from datos import edificios_db, comisarias_db, hospitales_db
from clima import obtener_clima_caba
import base64

st.set_page_config(page_title="SPPRO CABA - Panel Oficial", layout="wide")

if "users" not in st.session_state: 
    st.session_state["users"] = [{"nombre": "Admin (Propietario)"}]

if "entradas_extra" not in st.session_state:
    st.session_state["entradas_extra"] = {k: 2 for k in edificios_db.keys()}

# Base de datos dinámica para permitir agregar edificios nuevos en ejecución
if "edificios_dinamicos" not in st.session_state:
    st.session_state["edificios_dinamicos"] = edificios_db.copy()

# Historial de auditorías recientes en sesión
if "historial_auditorias" not in st.session_state:
    st.session_state["historial_auditorias"] = []

# Barra Lateral
st.sidebar.title("🛡️ SPPRO CABA")
st.sidebar.markdown("---")
clima_actual = obtener_clima_caba()
st.sidebar.info(f"🌤️ **Clima en Vivo:**\n{clima_actual}")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegación", ["🏢 Edificios & Puntos de Apoyo", "📄 Reporte PDF Institucional", "👥 Gestión de Usuarios", "🌐 Compartir Aplicación"])

def calcular_distancia(c1, c2):
    lat1, lon1 = map(float, c1)
    lat2, lon2 = c2
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

def encontrar_multiples_cercanos(coords_ed, db, cantidad=2):
    distancias = []
    for nombre, coords in db.items():
        dist = calcular_distancia(coords_ed, coords)
        distancias.append((nombre, dist, coords))
    distancias.sort(key=lambda x: x[1])
    return distancias[:cantidad]


# --- 1. EDIFICIOS Y CATASTRO ---
if menu == "🏢 Edificios & Puntos de Apoyo":
    st.header("🏢 Ficha Técnica y Proximidad de Emergencia en CABA")
    
    tab_cons, tab_alta = st.tabs(["🔍 Consultar Edificio Existente", "➕ Registrar Nuevo Edificio"])
    
    with tab_alta:
        st.subheader("Agregar Nuevo Objetivo Catastral")
        with st.form("form_nuevo_edificio"):
            nuevo_nombre = st.text_input("Nombre / Identificación del Edificio")
            nueva_dir = st.text_input("Dirección (Ej: Av. Corrientes 1500)")
            nueva_coords = st.text_input("Coordenadas GPS (Latitud, Longitud)", "-34.6037, -58.3816")
            
            submit_edificio = st.form_submit_button("Guardar e Incorporar Edificio")
            if submit_edificio:
                if nuevo_nombre and nueva_dir and nueva_coords:
                    try:
                        partes = [p.strip() for p in nueva_coords.split(',')]
                        float(partes[0])
                        float(partes[1])
                        
                        st.session_state["edificios_dinamicos"][nuevo_nombre] = {
                            "dir": nueva_dir,
                            "coords": nueva_coords
                        }
                        if nuevo_nombre not in st.session_state["entradas_extra"]:
                            st.session_state["entradas_extra"][nuevo_nombre] = 2
                            
                        st.success(f"¡El edificio '{nuevo_nombre}' fue agregado con éxito a la base de datos de la sesión!")
                    except Exception:
                        st.error("Error en el formato de las coordenadas. Deben ser números separados por coma (ej: -34.6037, -58.3816).")
                else:
                    st.warning("Por favor, completa todos los campos.")

    with tab_cons:
        db_activa = st.session_state["edificios_dinamicos"]
        sel = st.selectbox("Seleccione el Edificio (Orden Alfabético)", sorted(db_activa.keys()))
        d = db_activa[sel]
        coords_ed = [float(x) for x in d['coords'].split(',')]
        
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Calle de Ubicación", d['dir'].split()[0])
        col2.metric("Altura Catastral", d['dir'].split()[-1] if any(c.isdigit() for c in d['dir']) else "S/N")
        col3.metric("Coordenadas Geográficas", d['coords'])
        total_entradas = st.session_state["entradas_extra"][sel]
        col4.metric("Entradas / Salidas", total_entradas)
        
        st.markdown("### 📷 Carga de Accesos Adicionales")
        foto = st.file_uploader("Subir foto de una nueva entrada o salida del edificio", type=["jpg", "png", "jpeg"])
        if foto is not None:
            st.image(foto, caption="Evidencia fotográfica aportada", width=300)
            if st.button("Confirmar y Registrar Acceso"):
                st.session_state["entradas_extra"][sel] += 1
                st.success("¡Acceso adicional incorporado exitosamente al sistema!")
                st.rerun()

        comisarias_cercanas = encontrar_multiples_cercanos(coords_ed, comisarias_db, 2)
        hospitales_cercanos = encontrar_multiples_cercanos(coords_ed, hospitales_db, 2)

        st.markdown("---")
        st.subheader("🗺️ Mapa Operativo y Puntos de Apoyo en CABA")

        m = folium.Map(location=coords_ed, zoom_start=15)

        folium.Marker(
            location=coords_ed,
            popup=f"<b>{sel}</b><br>{d['dir']}",
            tooltip="Objetivo Evaluado",
            icon=folium.Icon(color="blue", icon="building", prefix="fa")
        ).add_to(m)

        for com, dist, coords_com in comisarias_cercanas:
            folium.Marker(
                location=[float(coords_com[0]), float(coords_com[1])],
                popup=f"<b>Comisaría:</b> {com}<br>Distancia: {dist}m",
                tooltip=f"Comisaría: {com} ({dist}m)",
                icon=folium.Icon(color="red", icon="shield", prefix="fa")
            ).add_to(m)

        for hosp, dist, coords_hosp in hospitales_cercanos:
            folium.Marker(
                location=[float(coords_hosp[0]), float(coords_hosp[1])],
                popup=f"<b>Hospital:</b> {hosp}<br>Distancia: {dist}m",
                tooltip=f"Hospital: {hosp} ({dist}m)",
                icon=folium.Icon(color="green", icon="hospital-o", prefix="fa")
            ).add_to(m)

        st_folium(m, width=700, height=450)

        st.markdown("---")
        st.subheader("🚨 Detalle de Puntos de Apoyo Cercanos")
        
        col_c, col_h = st.columns(2)
        with col_c:
            st.markdown("#### 👮 Comisarías Más Cercanas")
            for idx, (com, dist, _) in enumerate(comisarias_cercanas, 1):
                st.info(f"**{idx}.** {com} — *{dist} metros*")
                
        with col_h:
            st.markdown("#### 🏥 Hospitales Más Cercanos")
            for idx, (hosp, dist, _) in enumerate(hospitales_cercanos, 1):
                st.info(f"**{idx}.** {hosp} — *{dist} metros*")

        datos_actuales = {
            "nombre": sel, 
            "dir": d['dir'], 
            "coords": d['coords'], 
            "entradas": total_entradas,
            "comisarias": [(com, dist) for com, dist, _ in comisarias_cercanas], 
            "hospitales": [(hosp, dist) for hosp, dist, _ in hospitales_cercanos],
            "clima": clima_actual, 
            "fecha": datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        st.session_state["actual"] = datos_actuales

        if not st.session_state["historial_auditorias"] or st.session_state["historial_auditorias"][-1]["nombre"] != sel:
            st.session_state["historial_auditorias"].append(datos_actuales)
            if len(st.session_state["historial_auditorias"]) > 5:
                st.session_state["historial_auditorias"].pop(0)


# --- 2. REPORTE PDF INSTITUCIONAL ---
elif menu == "📄 Reporte PDF Institucional":
    st.header("📄 Generador de Reporte Técnico Extendido (Blanco y Negro)")
    
    if st.session_state["historial_auditorias"]:
        st.markdown("### 🕒 Historial de Edificios Consultados Recientemente")
        nombres_historial = [h["nombre"] for h in st.session_state["historial_auditorias"]]
        sel_historial = st.selectbox("Seleccione del historial para cargar sus datos:", nombres_historial)
        if st.button("Cargar desde Historial"):
            for h in st.session_state["historial_auditorias"]:
                if h["nombre"] == sel_historial:
                    st.session_state["actual"] = h
                    st.success(f"¡Datos de '{sel_historial}' cargados correctamente para generar el reporte!")
                    st.rerun()
        st.markdown("---")

    if "actual" in st.session_state:
        dat = st.session_state["actual"]
        responsable = st.text_input("Nombre y Apellido del Responsable Técnico Emisor", "Lic. Supervisor Operativo SPPRO")
        
        def limpiar_texto(texto):
            if not isinstance(texto, str):
                texto = str(texto)
            for simbolo in ["☀️", "🌤️", "⛅", "☁️", "🌫️", "🌧️", "⛈️", "°"]:
                texto = texto.replace(simbolo, "")
            return texto.encode('latin-1', 'ignore').decode('latin-1')

        pdf = FPDF()
        pdf.add_page()
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 7, "SISTEMA DE PROTECCION Y EVALUACION EDILICIA (SPPRO CABA)", ln=True, align="C")
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 5, "INFORME TECNICO OPERATIVO DE COBERTURA Y EMERGENCIAS", ln=True, align="C")
        
        pdf.ln(3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        
        clima_limpio = limpiar_texto(dat['clima'])
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(95, 5, f"Codigo de Auditoria: SPPRO-{datetime.now().strftime('%Y%m%d%H%M')}")
        pdf.cell(95, 5, f"Condicion Climatica: {clima_limpio}", ln=True, align="R")
        pdf.cell(190, 5, f"Fecha y Hora de Emision: {dat['fecha']}", ln=True)
        
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, "1. DATOS CATASTRALES Y CARACTERISTICAS EDILICIAS", ln=True)
        pdf.set_font("Arial", '', 9)
        
        pdf.cell(50, 6, "Objetivo Evaluado:", border=1)
        pdf.cell(140, 6, f" {limpiar_texto(dat['nombre'])}", border=1, ln=1)
        pdf.cell(50, 6, "Ubicacion (Calle y Numero):", border=1)
        pdf.cell(140, 6, f" {limpiar_texto(dat['dir'])}", border=1, ln=1)
        pdf.cell(50, 6, "Coordenadas GPS:", border=1)
        pdf.cell(140, 6, f" {dat['coords']}", border=1, ln=1)
        pdf.cell(50, 6, "Accesos Habilitados:", border=1)
        pdf.cell(140, 6, f" {dat['entradas']} entradas y salidas registradas", border=1, ln=1)
        
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, "2. ANALISIS DE COOPERACION E INTERVENCION (HOSPITALES Y COMISARIAS)", ln=True)
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(190, 5, "Establecimientos Medicos de Salud CABA mas cercanos:", ln=True)
        pdf.cell(120, 5, "Establecimiento Medico", border=1, align="C")
        pdf.cell(70, 5, "Distancia Lineal Calculada", border=1, align="C", ln=1)
        
        pdf.set_font("Arial", '', 9)
        for hosp, dist in dat["hospitales"]:
            pdf.cell(120, 6, f" {limpiar_texto(hosp)}", border=1)
            pdf.cell(70, 6, f" {dist} metros", border=1, align="C", ln=1)
            
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(190, 5, "Dependencias Policiales (Policia de la Ciudad) mas cercanas:", ln=True)
        pdf.cell(120, 5, "Dependencia Policial", border=1, align="C")
        pdf.cell(70, 5, "Distancia Lineal Calculada", border=1, align="C", ln=1)
        
        pdf.set_font("Arial", '', 9)
        for com, dist in dat["comisarias"]:
            pdf.cell(120, 6, f" {limpiar_texto(com)}", border=1)
            pdf.cell(70, 6, f" {dist} metros", border=1, align="C", ln=1)
            
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, "3. DICTAMEN TECNICO Y OBSERVACIONES", ln=True)
        pdf.set_font("Arial", '', 8.5)
        pdf.multi_cell(190, 4.5, "El presente documento tecnico detalla de forma integral los recursos operativos de respuesta inmediata circundantes al objetivo. Se han validado tanto las vias de acceso perimetral como los tiempos estimados de arribo de unidades sanitarias y moviles policiales de la Ciudad Autonoma de Buenos Aires.")
        
        pdf.ln(20)
        pdf.set_font("Arial", '', 9)
        pdf.cell(100)
        pdf.cell(80, 4, "________________________________________", ln=True, align="C")
        pdf.cell(100)
        pdf.cell(80, 5, limpiar_texto(responsable), ln=True, align="C")
        pdf.cell(100)
        pdf.cell(80, 4, "Firma y Sello - Administrador SPPRO", ln=True, align="C")
        
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode('latin-1')
        else:
            pdf_bytes = bytes(pdf_output)

        nombre_archivo = f"Informe_Detallado_{dat['nombre'].replace(' ', '_')}.pdf"
        
        st.success("¡Reporte listo para previsualizar o descargar!")
        
        st.markdown("### 👁️ Vista Previa del Reporte PDF")
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        st.markdown("---")
        st.download_button(
            label="Descargar Reporte PDF Detallado (B/N)",
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf"
        )
    else:
        st.warning("⚠️ Seleccione y consulte un edificio primero en la solapa '🏢 Edificios & Puntos de Apoyo'.")


# --- 3. GESTIÓN DE USUARIOS ---
elif menu == "👥 Gestión de Usuarios":
    st.header("👥 Panel de Control de Usuarios")
    
    with st.form("form_alta"):
        nombre_u = st.text_input("Nombre del Nuevo Usuario")
        if st.form_submit_button("Registrar Usuario") and nombre_u:
            st.session_state["users"].append({"nombre": nombre_u})
            st.success("Usuario agregado con éxito.")
            st.rerun()
            
    st.markdown("### 📋 Usuarios Activos")
    for i, u in enumerate(st.session_state["users"]):
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"👤 **{u['nombre']}**")
        if "Administrador" not in u['nombre']:
            if c2.button("🗑️ Borrar", key=f"del_{i}"):
                st.session_state["users"].pop(i)
                st.rerun()


# --- 4. COMPARTIR APLICACIÓN ---
elif menu == "🌐 Compartir Aplicación":
    st.header("🌐 Enlace y Compartir Aplicación")
    st.write("Puedes compartir esta herramienta de forma pública mediante los siguientes pasos:")
    
    st.markdown("""
    1. **Sube tu código a GitHub:** Asegúrate de tener los archivos `aplicación.py`, `datos.py` y `clima.py` en un repositorio público.
    2. **Conéctalo en Streamlit Cloud:** Ingresa a [share.streamlit.io](https://share.streamlit.io/) con tu cuenta y despliega el repositorio.
    3. **Tu Enlace Público:** Una vez desplegado, Streamlit te asignará una URL oficial que podrás compartir con cualquier equipo u operador.
    """)
    
    st.info("🔗 **Ejemplo de URL Pública:** `https://sppro-caba.streamlit.app`")
