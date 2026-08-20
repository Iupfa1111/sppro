import sqlite3
import streamlit as st
from fpdf import FPDF
import pandas as pd
import datetime
import clima 

# --- CONFIGURACIÓN Y BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT, activo INTEGER, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS edificios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, direccion TEXT, altura TEXT, latitud REAL, longitud REAL, observaciones TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS puntos_apoyo (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, tipo TEXT, direccion TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, objetivo TEXT, fecha TIMESTAMP)")
    
    # Usuario por defecto
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin123', 1, 'Administrador')")
    conn.commit()
    conn.close()

init_db()

# --- CLASE PARA PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 18)
        self.cell(0, 10, "VERIFICACION INTELIGENTE DE EDIFICIOS (SPPRO)", ln=True, align="C")
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "by Angel Ibañez", align="C")

# --- FUNCIONES ---
def registrar_auditoria(user, obj):
    conn = sqlite3.connect("sppro.db")
    conn.execute("INSERT INTO auditoria (usuario, objetivo, fecha) VALUES (?, ?, ?)", (user, obj, datetime.datetime.now()))
    conn.commit()
    conn.close()

def traducir_estado_clima(e):
    trads = {"clear sky": "Despejado", "few clouds": "Pocas nubes", "broken clouds": "Nublado", "rain": "Lluvia"}
    return trads.get(e.lower(), e.capitalize())

# --- INTERFAZ ---
st.set_page_config(page_title="SPPRO", layout="wide")

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("SPPRO | Acceso")
    u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        conn = sqlite3.connect("sppro.db")
        user = conn.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (u, p)).fetchone()
        conn.close()
        if user:
            st.session_state["logged_in"] = True; st.session_state["username"] = u; st.session_state["user_role"] = user[3]; st.rerun()
        else: st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.title(f"SPPRO | {st.session_state['username']}")
menu = st.sidebar.radio("Navegación", ["Verificación", "Gestionar Puntos", "Auditoría"])

# --- SECCIONES ---
if menu == "Verificación":
    st.header("Verificación de Edificios")
    emblematicos = {"Casa Rosada": {"dir": "Balcarce 50", "lat": -34.608, "lon": -58.370, "altura": "50"}, "Palacio Barolo": {"dir": "Av. de Mayo 1370", "lat": -34.611, "lon": -58.385, "altura": "1370"}}
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 Edificios Emblemáticos"): st.session_state["modo"] = "lista"
    with col2:
        if st.button("📝 Ingreso Manual"): st.session_state["modo"] = "manual"

    datos = None
    if "modo" in st.session_state:
        if st.session_state["modo"] == "lista":
            sel = st.selectbox("Seleccionar:", list(emblematicos.keys()))
            datos = {"nombre": sel, **emblematicos[sel], "obs": ""}
        else:
            with st.form("manual"):
                n = st.text_input("Nombre"); d = st.text_input("Dirección"); a = st.text_input("Altura")
                lat = st.number_input("Latitud", format="%.6f"); lon = st.number_input("Longitud", format="%.6f"); obs = st.text_area("Obs")
                if st.form_submit_button("Cargar"): datos = {"nombre": n, "dir": d, "altura": a, "lat": lat, "lon": lon, "obs": obs}

    if datos and st.button("✅ VERIFICAR OBJETIVO", type="primary"): st.session_state["verificado"] = datos

    if "verificado" in st.session_state:
        obj = st.session_state["verificado"]
        st.write(f"### Objetivo: {obj['nombre']} | Dir: {obj['dir']}")
        
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"1. DATOS: {obj['nombre']} | {obj['dir']}", ln=True)
        pdf.cell(0, 10, f"2. GEOGRAFIA: Alt {obj['altura']} | Lat {obj['lat']} | Lon {obj['lon']}", ln=True)
        pdf.cell(0, 10, "3. PUNTOS SEGUROS:", ln=True)
        conn = sqlite3.connect("sppro.db")
        pts = conn.execute("SELECT tipo, nombre, direccion FROM puntos_apoyo WHERE tipo IN ('Hospitales', 'Comisarias', 'Comisaría')").fetchall()
        conn.close()
        for p in pts: pdf.cell(0, 7, f"- {p[0]}: {p[1]} ({p[2]})", ln=True)
        
        clima_data = clima.obtener_clima()
        pdf.cell(0, 10, f"4. CLIMA: {traducir_estado_clima(clima_data['estado'])} | Temp: {clima_data['temperatura']}", ln=True)
        pdf.ln(20)
        pdf.cell(0, 10, "Firma del Operador: _________", ln=True)
        
        if st.download_button("📥 Descargar PDF Profesional", pdf.output(dest='S').encode('latin-1'), "informe_SPPRO.pdf", "application/pdf"):
            registrar_auditoria(st.session_state["username"], obj['nombre'])

elif menu == "Gestionar Puntos":
    with st.form("punto"):
        n = st.text_input("Nombre"); t = st.selectbox("Tipo", ["Hospitales", "Comisarias", "Fuerzas de Seguridad"]); d = st.text_input("Dirección")
        if st.form_submit_button("Agregar"):
            conn = sqlite3.connect("sppro.db")
            conn.execute("INSERT INTO puntos_apoyo (nombre, tipo, direccion) VALUES (?, ?, ?)", (n, t, d))
            conn.commit(); conn.close(); st.success("Agregado")

elif menu == "Auditoría" and st.session_state["user_role"] == "Administrador":
    conn = sqlite3.connect("sppro.db")
    st.dataframe(pd.read_sql("SELECT * FROM auditoria ORDER BY fecha DESC", conn))
    conn.close()
