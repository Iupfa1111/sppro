import sqlite3
import streamlit as st
from fpdf import FPDF
import pandas as pd
import datetime
import clima

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT, activo INTEGER, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS puntos_apoyo (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, tipo TEXT, direccion TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, objetivo TEXT, fecha TIMESTAMP)")
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin123', 1, 'Administrador')")
    conn.commit()
    conn.close()

init_db()

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "VERIFICACION INTELIGENTE DE EDIFICIOS (SPPRO)", ln=True, align="C")
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "by Angel Ibañez", align="C")

# --- DATOS: LOS 30 EDIFICIOS ---
edificios_caba = {
    "Casa Rosada": {"dir": "Balcarce 50", "lat": -34.608, "lon": -58.370, "alt": "50"},
    "Palacio Barolo": {"dir": "Av. de Mayo 1370", "lat": -34.611, "lon": -58.385, "alt": "1370"},
    "Edificio Kavanagh": {"dir": "Florida 1065", "lat": -34.593, "lon": -58.374, "alt": "1065"},
    "Congreso de la Nación": {"dir": "Av. Entre Ríos 179", "lat": -34.609, "lon": -58.390, "alt": "179"},
    "Teatro Colón": {"dir": "Cerrito 628", "lat": -34.601, "lon": -58.383, "alt": "628"},
    "Cabildo de Buenos Aires": {"dir": "Bolívar 65", "lat": -34.608, "lon": -58.373, "alt": "65"},
    "Catedral Metropolitana": {"dir": "San Martín 27", "lat": -34.607, "lon": -58.374, "alt": "27"},
    "Centro Cultural Kirchner": {"dir": "Sarmiento 151", "lat": -34.604, "lon": -58.368, "alt": "151"},
    "Torre Monumental": {"dir": "Av. Ramos Mejía 1315", "lat": -34.590, "lon": -58.373, "alt": "1315"},
    "Palacio de Aguas Corrientes": {"dir": "Av. Córdoba 1950", "lat": -34.599, "lon": -58.395, "alt": "1950"},
    "Café Tortoni": {"dir": "Av. de Mayo 825", "lat": -34.608, "lon": -58.378, "alt": "825"},
    "Manzana de las Luces": {"dir": "Venezuela 469", "lat": -34.610, "lon": -58.373, "alt": "469"},
    "El Ateneo Grand Splendid": {"dir": "Av. Santa Fe 1860", "lat": -34.598, "lon": -58.393, "alt": "1860"},
    "Palacio Duhau": {"dir": "Av. Alvear 1661", "lat": -34.590, "lon": -58.388, "alt": "1661"},
    "Cementerio de La Recoleta": {"dir": "Junín 1760", "lat": -34.588, "lon": -58.392, "alt": "1760"},
    "Usina del Arte": {"dir": "Caffarena 1", "lat": -34.626, "lon": -58.361, "alt": "1"},
    "Hipódromo de Palermo": {"dir": "Av. del Libertador 4101", "lat": -34.568, "lon": -58.423, "alt": "4101"},
    "Facultad de Derecho (UBA)": {"dir": "Av. Figueroa Alcorta 2263", "lat": -34.583, "lon": -58.391, "alt": "2263"},
    "Museo Nacional Bellas Artes": {"dir": "Av. Libertador 1473", "lat": -34.583, "lon": -58.393, "alt": "1473"},
    "Estadio Monumental": {"dir": "Av. Figueroa Alcorta 7597", "lat": -34.545, "lon": -58.449, "alt": "7597"},
    "Edificio Comega": {"dir": "Av. Corrientes 222", "lat": -34.604, "lon": -58.369, "alt": "222"},
    "Edificio Safico": {"dir": "Av. Corrientes 456", "lat": -34.603, "lon": -58.374, "alt": "456"},
    "Galería Güemes": {"dir": "Florida 165", "lat": -34.606, "lon": -58.373, "alt": "165"},
    "Palacio Pereda": {"dir": "Arroyo 1130", "lat": -34.591, "lon": -58.383, "alt": "1130"},
    "Librería de Ávila": {"dir": "Alsina 500", "lat": -34.609, "lon": -58.375, "alt": "500"},
    "Tribunales Federales": {"dir": "Talcahuano 550", "lat": -34.602, "lon": -58.384, "alt": "550"},
    "Centro Naval": {"dir": "Florida 300", "lat": -34.596, "lon": -58.377, "alt": "300"},
    "Banco de Boston": {"dir": "Diagonal Norte 600", "lat": -34.604, "lon": -58.377, "alt": "600"},
    "Jardín Botánico": {"dir": "Av. Santa Fe 3951", "lat": -34.581, "lon": -58.411, "alt": "3951"},
    "Palacio Estrugamou": {"dir": "Juncal 783", "lat": -34.594, "lon": -58.380, "alt": "783"}
}

# --- INTERFAZ ---
st.set_page_config(page_title="SPPRO", layout="wide")

if "logged_in" not in st.session_state: 
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("SPPRO | Acceso")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        conn = sqlite3.connect("sppro.db")
        user = conn.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (u, p)).fetchone()
        conn.close()
        if user:
            st.session_state["logged_in"] = True
            st.session_state["username"] = u
            st.session_state["user_role"] = user[3]
            st.rerun()
        else: 
            st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.title(f"SPPRO | {st.session_state['username']}")
menu = st.sidebar.radio("Navegación", ["Verificación", "Gestionar Puntos", "Auditoría"])

if menu == "Verificación":
    st.header("Verificación de Edificios")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏢 Selección de Emblemáticos"): 
            st.session_state["modo"] = "lista"
    with c2:
        if st.button("📝 Ingreso Manual"): 
            st.session_state["modo"] = "manual"

    datos = None
    if "modo" in st.session_state:
        if st.session_state["modo"] == "lista":
            sel = st.selectbox("Seleccionar edificio:", list(edificios_caba.keys()))
            datos = {"nombre": sel, **edificios_caba[sel]}
        else:
            with st.form("manual"):
                n = st.text_input("Nombre")
                d = st.text_input("Dirección")
                alt = st.text_input("Altura")
                lat = st.number_input("Latitud", format="%.6f")
                lon = st.number_input("Longitud", format="%.6f")
                if st.form_submit_button("Cargar"): 
                    datos = {"nombre": n, "dir": d, "lat": lat, "lon": lon, "alt": alt}

    if datos and st.button("✅ VERIFICAR OBJETIVO", type="primary"): 
        st.session_state["verificado"] = datos

    if "verificado" in st.session_state:
        obj = st.session_state["verificado"]
        st.write(f"### Objetivo: {obj['nombre']} | Dir: {obj['dir']}")
        
        # Generar PDF
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"1. DATOS DEL EVENTO: {obj['nombre']} | {obj['dir']}", ln=True)
        pdf.cell(0, 10, f"2. CONTEXTO GEOGRAFICO: Alt {obj.get('alt','N/A')} | Lat {obj['lat']} | Lon {obj['lon']}", ln=True)
        pdf.cell(0, 10, "3. PUNTOS SEGUROS ESTRATEGICOS:", ln=True)
        
        conn = sqlite3.connect("sppro.db")
        pts = conn.execute("SELECT tipo, nombre, direccion FROM puntos_apoyo").fetchall()
        conn.close()
        for p in pts: 
            pdf.cell(0, 7, f"- {p[0]}: {p[1]} ({p[2]})", ln=True)
        
        clima_d = clima.obtener_clima()
        estado_clima = clima_d.get('estado', 'Despejado') if clima_d else 'No disponible'
        temp_clima = clima_d.get('temperatura', 'N/A') if clima_d else 'N/A'
        
        pdf.cell(0, 10, f"4. CLIMA: {estado_clima} | Temp: {temp_clima}", ln=True)
        pdf.ln(20)
        pdf.cell(0, 10, "Firma del Operador: _________", ln=True)
        
        if st.download_button("📥 Descargar Informe PDF", pdf.output(dest='S').encode('latin-1'), "informe_SPPRO.pdf", "application/pdf"):
            conn = sqlite3.connect("sppro.db")
            conn.execute("INSERT INTO auditoria (usuario, objetivo, fecha) VALUES (?, ?, ?)", 
                         (st.session_state["username"], obj['nombre'], datetime.datetime.now()))
            conn.commit()
            conn.close()

elif menu == "Gestionar Puntos":
    st.subheader("Administrar Puntos de Apoyo")
    with st.form("punto"):
        n = st.text_input("Nombre")
        t = st.selectbox("Tipo", ["Hospitales", "Comisarias", "Fuerzas de Seguridad"])
        d = st.text_input("Dirección")
        if st.form_submit_button("Agregar punto"):
            conn = sqlite3.connect("sppro.db")
            conn.execute("INSERT INTO puntos_apoyo (nombre, tipo, direccion) VALUES (?, ?, ?)", (n, t, d))
            conn.commit()
            conn.close()
            st.success("Punto agregado correctamente.")

elif menu == "Auditoría":
    if st.session_state["user_role"] == "Administrador":
        st.subheader("Registro de Auditoría")
        conn = sqlite3.connect("sppro.db")
        st.dataframe(pd.read_sql("SELECT * FROM auditoria ORDER BY fecha DESC", conn))
        conn.close()
    else:
        st.error("Acceso restringido")
