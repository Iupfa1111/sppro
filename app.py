# aplicación.py
import streamlit as st
import math
from datetime import datetime
from fpdf import FPDF
from datos import edificios_db, puntos_seguros
from clima import obtener_clima_caba

st.set_page_config(page_title="SPPRO CABA - Panel Oficial", layout="wide")

# Estado persistente
if "users" not in st.session_state: 
    st.session_state["users"] = ["Admin", "Supervisor Zonal"]

# Barra lateral con Clima en Tiempo Real
st.sidebar.title("🛡️ SPPRO CABA")
st.sidebar.markdown("---")
st.sidebar.subheader("📡 Condiciones Climáticas")
st.sidebar.info(f"**CABA En Vivo:**\n{obtener_clima_caba()}")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegación", ["🏢 Edificios & Cobertura", "📄 Reportes Ejecutivos", "👥 Gestión de Usuarios"])

# Función para calcular distancia exacta en metros
def calcular_distancia(c1, c2):
    lat1, lon1 = map(float, c1)
    lat2, lon2 = c2
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

if menu == "🏢 Edificios & Cobertura":
    st.header("🏢 Verificación y Cobertura de Edificios")
    
    # Listado ordenado alfabéticamente
    sel = st.selectbox("Seleccionar Edificio", sorted(edificios_db.keys()))
    
    if st.button("Verificar Proximidad"):
        d = edificios_db[sel]
        coords_ed = d['coords'].split(',')
        
        # Encontrar el punto de seguridad/hospital más cercano
        punto_cercano = min(
            puntos_seguros, 
            key=lambda x: ((puntos_seguros[x][0]-float(coords_ed[0]))**2 + (puntos_seguros[x][1]-float(coords_ed[1]))**2)**0.5
        )
        distancia = calcular_distancia(coords_ed, puntos_seguros[punto_cercano])
        
        st.session_state["actual"] = {
            "nombre": sel,
            "dir": d['dir'],
            "coords": d['coords'],
            "punto": punto_cercano,
            "dist": distancia,
            "fecha": datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Dirección", d['dir'])
        col2.metric("Punto de Apoyo Cercano", punto_cercano)
        col3.metric("Distancia", f"{distancia} metros")
        st.success("Verificación completada con éxito.")

elif menu == "📄 Reportes Ejecutivos":
    st.header("📄 Generador de Reporte Técnico Oficial")
    
    if "actual" in st.session_state:
        dat = st.session_state["actual"]
        responsable = st.text_input("Nombre del Inspector / Responsable", "Inspector General")
        
        if st.button("Generar PDF Profesional"):
            pdf = FPDF()
            pdf.add_page()
            
            # Cabecera Institucional Azul
            pdf.set_fill_color(24, 43, 73)
            pdf.rect(0, 0, 210, 35, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 18)
            pdf.set_xy(10, 12)
            pdf.cell(190, 10, "INFORME TÉCNICO DE SEGURIDAD SPPRO", ln=True, align="C")
            
            # Metadatos
            pdf.set_text_color(0, 0, 0)
            pdf.ln(15)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 8, f"ID de Reporte: SPPRO-{datetime.now().strftime('%Y%m%d%H%M')}", ln=True)
            pdf.cell(190, 8, f"Fecha de Emisión: {dat['fecha']}", ln=True)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 8, "1. DATOS DEL OBJETIVO", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(50, 8, "Edificio:", border=1, fill=True)
            pdf.cell(140, 8, f" {dat['nombre']}", border=1, ln=1)
            pdf.cell(50, 8, "Dirección:", border=1, fill=True)
            pdf.cell(140, 8, f" {dat['dir']}", border=1, ln=1)
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 8, "2. ANÁLISIS DE COBERTURA", ln=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(95, 8, "Dependencia / Hospital más cercano", border=1, fill=True, align="C")
            pdf.cell(95, 8, "Distancia Lineal", border=1, fill=True, align="C")
            pdf.ln(8)
            pdf.set_font("Arial", '', 11)
            pdf.cell(95, 10, f" {dat['punto']}", border=1, align="C")
            pdf.cell(95, 10, f" {dat['dist']} metros", border=1, align="C", ln=1)
            
            # Firma
            pdf.ln(30)
            pdf.cell(100)
            pdf.cell(80, 5, "________________________________________", ln=True, align="C")
            pdf.cell(100)
            pdf.cell(80, 10, responsable, ln=True, align="C")
            
            archivo = "reporte_oficial.pdf"
            pdf.output(archivo)
            
            with open(archivo, "rb") as f:
                st.download_button("📥 Descargar Reporte PDF", f, file_name=f"Reporte_{dat['nombre'].replace(' ', '_')}.pdf")
    else:
        st.warning("⚠️ Primero debes verificar un edificio en la solapa '🏢 Edificios & Cobertura'.")

elif menu == "👥 Gestión de Usuarios":
    st.header("👥 Control de Usuarios")
    nuevo = st.text_input("Nuevo usuario")
    if st.button("Agregar"):
        if nuevo and nuevo not in st.session_state["users"]:
            st.session_state["users"].append(nuevo)
            st.success("Usuario agregado.")
            
    st.subheader("Usuarios Registrados")
    for i, u in enumerate(st.session_state["users"]):
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"👤 {u}")
        if u != "Admin":
            if c2.button("🗑️", key=f"del_{i}"):
                st.session_state["users"].pop(i)
                st.rerun()
