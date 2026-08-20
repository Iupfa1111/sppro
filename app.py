import streamlit as st
import math
from datetime import datetime
from fpdf import FPDF
from datos import edificios_db, puntos_seguros

st.set_page_config(page_title="SPPRO v4.0", layout="wide")

# Inicialización de estado
if "users" not in st.session_state: st.session_state["users"] = ["Admin"]
if "logs" not in st.session_state: st.session_state["logs"] = []

def calcular_distancia(c1, c2):
    lat1, lon1 = map(float, c1); lat2, lon2 = c2
    R = 6371000
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(math.radians(lon2-lon1)/2)**2
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

st.sidebar.title("🛡️ SPPRO v4.0")
menu = st.sidebar.radio("Navegación", ["🏢 Edificios", "📄 Reportes", "👥 Usuarios"])

if menu == "🏢 Edificios":
    st.header("Verificación de Edificios")
    sel = st.selectbox("Seleccionar Edificio", sorted(edificios_db.keys()))
    if st.button("Verificar"):
        d = edificios_db[sel]
        c = min(puntos_seguros, key=lambda x: ((puntos_seguros[x][0]-float(d['coords'].split(',')[0]))**2 + (puntos_seguros[x][1]-float(d['coords'].split(',')[1]))**2)**0.5)
        dist = calcular_distancia(d['coords'].split(','), puntos_seguros[c])
        st.session_state.update({"sel": sel, "punto": c, "dist": dist})
        st.success(f"Edificio: {sel} | Distancia a {c}: {dist} metros")

elif menu == "📄 Reportes":
    st.header("Generar Reporte PDF")
    firma = st.text_input("Firma del Responsable")
    if st.button("Crear PDF Profesional"):
        pdf = FPDF(); pdf.add_page(); pdf.set_fill_color(24, 43, 73); pdf.rect(0, 0, 210, 30, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 20); pdf.cell(190, 20, "REPORTE OFICIAL SPPRO", ln=True, align="C")
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", '', 12); pdf.ln(10)
        pdf.cell(190, 10, f"ID Reporte: SPPRO-{datetime.now().strftime('%Y%m%d%H%M')}", ln=True)
        pdf.cell(190, 10, f"Edificio: {st.session_state.get('sel', 'N/A')}", ln=True)
        pdf.cell(190, 10, f"Punto Seguridad: {st.session_state.get('punto', 'N/A')} ({st.session_state.get('dist', '0')} m)", ln=True)
        pdf.ln(20); pdf.cell(100); pdf.cell(80, 5, "_________________________", ln=True, align="C")
        pdf.cell(100); pdf.cell(80, 10, firma, ln=True, align="C")
        pdf.output("reporte.pdf")
        with open("reporte.pdf", "rb") as f: st.download_button("📥 Descargar", f, "reporte.pdf")

elif menu == "👥 Usuarios":
    st.header("Gestión de Usuarios")
    nuevo = st.text_input("Nuevo usuario")
    if st.button("Agregar"): st.session_state["users"].append(nuevo)
    for i, u in enumerate(st.session_state["users"]):
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"👤 {u}")
        if u != "Admin" and c2.button("🗑️", key=f"del_{i}"): st.session_state["users"].pop(i); st.rerun()
