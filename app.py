# app.py
from datetime import datetime
from fpdf import FPDF
import requests
import streamlit as st
from datos import edificios_db, puntos_seguros

st.set_page_config(page_title="SPPRO CABA", layout="wide")

if "auditoria" not in st.session_state: st.session_state["auditoria"] = []

def obtener_clima():
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast?latitude=-34.61&longitude=-58.37&current=temperature_2m", timeout=2)
        return f"{r.json()['current']['temperature_2m']} C"
    except: return "No disponible"

with st.sidebar:
    st.title("🛡️ SPPRO v3.6")
    menu = st.radio("Navegación", ["1️⃣ Edificios", "2️⃣ PDF", "3️⃣ Auditoría"])

if menu == "1️⃣ Edificios":
    st.header("🏢 Verificación de Edificios")
    st.metric("🌡️ Clima CABA", obtener_clima())
    sel = st.selectbox("Seleccionar", sorted(list(edificios_db.keys())))
    
    if st.button("🔍 VERIFICAR"):
        st.session_state["act"] = (sel, edificios_db[sel])
    
    if "act" in st.session_state:
        nom, dat = st.session_state["act"]
        st.success(f"Objetivo: {nom}")
        st.write(f"📍 {dat['dir']} | 📏 {dat['alt']}")
        
        lat, lon = map(float, dat['coords'].split(','))
        cercano = min(puntos_seguros, key=lambda x: ((puntos_seguros[x][0]-lat)**2 + (puntos_seguros[x][1]-lon)**2)**0.5)
        st.info(f"🛡️ Punto seguro más cercano: **{cercano}**")

elif menu == "2️⃣ PDF":
    st.header("📄 Generador PDF")
    if "act" in st.session_state:
        nom, dat = st.session_state["act"]
        firma = st.text_input("Firma Digital")
        if st.button("📥 Generar PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, "REPORTE SPPRO", ln=True, align="C")
            pdf.set_font("Arial", '', 11)
            pdf.cell(200, 10, f"Edificio: {nom}", ln=True)
            pdf.cell(200, 10, f"Dirección: {dat['dir']}", ln=True)
            pdf.cell(200, 10, f"Firmante: {firma}", ln=True)
            
            pdf.output("reporte.pdf")
            st.session_state["auditoria"].append(f"{nom} - {firma}")
            with open("reporte.pdf", "rb") as f:
                st.download_button("Descargar", f, "reporte.pdf")
    else: st.warning("Seleccione un edificio primero.")

elif menu == "3️⃣ Auditoría":
    st.header("📊 Historial")
    for reg in st.session_state["auditoria"]:
        st.write(f"✅ {reg}")
