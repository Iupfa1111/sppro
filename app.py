# aplicación.py
import streamlit as st
import math
from datetime import datetime
from fpdf import FPDF
from datos import edificios_db, puntos_seguros
from clima import obtener_clima_caba

st.set_page_config(page_title="SPPRO CABA - Panel Oficial", layout="wide")

# Gestión de Usuarios y Permisos (Administrador)
if "users" not in st.session_state: 
    st.session_state["users"] = [{"nombre": "Admin (Propietario)", "rol": "Administrador"}]

# Base de datos en memoria para entradas/salidas adicionales de edificios
if "entradas_extra" not in st.session_state:
    st.session_state["entradas_extra"] = {k: 2 for k in edificios_db.keys()}

# --- BARRA LATERAL ---
st.sidebar.title("🛡️ SPPRO CABA")
st.sidebar.markdown("---")
st.sidebar.subheader("📡 Clima en Tiempo Real")
clima_actual = obtener_clima_caba()
st.sidebar.info(f"**CABA:** {clima_actual}")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegación", ["🏢 Edificios & Catastro", "📄 Reportes Ejecutivos PDF", "👥 Gestión de Usuarios", "🌐 Compartir Aplicación"])

# Función para calcular distancia lineal
def calcular_distancia(c1, c2):
    lat1, lon1 = map(float, c1)
    lat2, lon2 = c2
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# --- SOLAPA 1: EDIFICIOS Y CATASTRO ---
if menu == "🏢 Edificios & Catastro":
    st.header("🏢 Ficha Técnica y Catastro de Edificios CABA")
    
    sel = st.selectbox("Seleccione el Edificio (Orden Alfabético)", sorted(edificios_db.keys()))
    d = edificios_db[sel]
    
    # Datos catastrales y de ubicación
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Calle Ubicación", d['dir'].split()[0])
    col2.metric("Altura Catastral", d['dir'].split()[-1] if any(char.isdigit() for char in d['dir']) else "S/N")
    col3.metric("Coordenadas", d['coords'])
    total_entradas = st.session_state["entradas_extra"][sel]
    col4.metric("Entradas / Salidas", total_entradas)
    
    st.markdown("### 📷 Registro de Nuevas Entradas y Salidas")
    st.write("Si conoce una entrada o salida adicional que la app no registra, suba una foto probatoria para sumarla automáticamente al sistema:")
    
    foto_subida = st.file_uploader("Subir imagen de la nueva entrada/salida", type=["jpg", "png", "jpeg"])
    if foto_subida is not None:
        st.image(foto_subida, caption="Evidencia fotográfica aportada", width=300)
        if st.button("Confirmar y Agregar Entrada"):
            st.session_state["entradas_extra"][sel] += 1
            st.success(f"¡Entrada agregada con éxito! El edificio ahora cuenta con {st.session_state['entradas_extra'][sel]} accesos.")
            st.rerun()

    # Cálculo de Cobertura de Emergencia
    coords_ed = d['coords'].split(',')
    punto_cercano = min(
        puntos_seguros, 
        key=lambda x: ((puntos_seguros[x][0]-float(coords_ed[0]))**2 + (puntos_seguros[x][1]-float(coords_ed[1]))**2)**0.5
    )
    distancia = calcular_distancia(coords_ed, puntos_seguros[punto_cercano])
    
    st.markdown("---")
    st.info(f"🚨 **Dependencia de Apoyo más cercana:** {punto_cercano} (a {distancia} metros lineales).")
    
    # Guardar estado actual para el PDF
    st.session_state["actual"] = {
        "nombre": sel,
        "dir": d['dir'],
        "coords": d['coords'],
        "entradas": total_entradas,
        "punto": punto_cercano,
        "dist": distancia,
        "clima": clima_actual,
        "fecha": datetime.now().strftime('%d/%m/%Y %H:%M')
    }

# --- SOLAPA 2: REPORTES PDF ---
elif menu == "📄 Reportes Ejecutivos PDF":
    st.header("📄 Generador de Reporte Técnico Oficial")
    
    if "actual" in st.session_state:
        dat = st.session_state["actual"]
        responsable = st.text_input("Administrador Responsable Emisor", "Administrador General SPPRO")
        
        if st.button("Generar PDF Profesional"):
            pdf = FPDF()
            pdf.add_page()
            
            # Cabecera Institucional Azul
            pdf.set_fill_color(24, 43, 73)
            pdf.rect(0, 0, 210, 40, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 16)
            pdf.set_xy(10, 15)
            pdf.cell(190, 8, "SISTEMA DE PROTECCIÓN Y GUBERNAMENTAL (SPPRO CABA)", ln=True, align="C")
            
            # Metadatos del Reporte y Clima
            pdf.set_text_color(0, 0, 0)
            pdf.ln(18)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(95, 6, f"ID Reporte: SPPRO-{datetime.now().strftime('%Y%m%d%H%M')}")
            pdf.cell(95, 6, f"Clima en Vivo: {dat['clima']}", ln=True, align="R")
            pdf.cell(190, 6, f"Fecha y Hora de Emision: {dat['fecha']}", ln=True)
            
            # Sección 1: Catastro
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 8, "1. INFORMACION CATASTRAL Y EDILICIA", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(50, 7, "Objetivo:", border=1, fill=True)
            pdf.cell(140, 7, f" {dat['nombre']}", border=1, ln=1)
            pdf.cell(50, 7, "Ubicacion (Calle):", border=1, fill=True)
            pdf.cell(140, 7, f" {dat['dir']}", border=1, ln=1)
            pdf.cell(50, 7, "Coordenadas:", border=1, fill=True)
            pdf.cell(140, 7, f" {dat['coords']}", border=1, ln=1)
            pdf.cell(50, 7, "Accesos Totales:", border=1, fill=True)
            pdf.cell(140, 7, f" {dat['entradas']} entradas/salidas registradas", border=1, ln=1)
            
            # Sección 2: Cobertura
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 8, "2. COBERTURA DE SEGURIDAD Y EMERGENCIAS", ln=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(110, 7, "Dependencia / Hospital Cercano", border=1, fill=True, align="C")
            pdf.cell(80, 7, "Distancia Lineal", border=1, fill=True, align="C")
            pdf.ln(7)
            pdf.set_font("Arial", '', 10)
            pdf.cell(110, 8, f" {dat['punto']}", border=1)
            pdf.cell(80, 8, f" {dat['dist']} metros", border=1, align="C", ln=1)
            
            # Firma del Administrador
            pdf.ln(35)
            pdf.cell(100)
            pdf.cell(80, 5, "________________________________________", ln=True, align="C")
            pdf.cell(100)
            pdf.cell(80, 8, responsable, ln=True, align="C")
            pdf.cell(100)
            pdf.cell(80, 5, "Administrador Autorizado", ln=True, align="C")
            
            archivo = "reporte_tecnico_sppro.pdf"
            pdf.output(archivo)
            
            with open(archivo, "rb") as f:
                st.download_button("📥 Descargar Reporte PDF Oficial", f, file_name=f"Reporte_{dat['nombre'].replace(' ', '_')}.pdf")
    else:
        st.warning("⚠️ Seleccione y consulte un edificio primero en la solapa '🏢 Edificios & Catastro'.")

# --- SOLAPA 3: GESTIÓN DE USUARIOS (ADMINISTRADOR) ---
elif menu == "👥 Gestión de Usuarios":
    st.header("👥 Panel de Control de Usuarios (Potestad de Administrador)")
    st.write("Como administrador, tienes la potestad exclusiva de dar alta o baja a los usuarios del sistema.")
    
    with st.form("form_usuario"):
        nuevo_nombre = st.text_input("Nombre del Nuevo Usuario")
        nuevo_rol = st.selectbox("Rol Asignado", ["Operador Zonal", "Inspector", "Supervisor"])
        btn_crear = st.form_submit_button("Dar de Alta Usuario")
        
        if btn_crear and nuevo_nombre:
            st.session_state["users"].append({"nombre": nuevo_nombre, "rol": nuevo_rol})
            st.success(f"Usuario '{nuevo_nombre}' agregado correctamente.")
            st.rerun()
            
    st.markdown("### 📋 Usuarios Activos en el Sistema")
    for i, u in enumerate(st.session_state["users"]):
        col_u1, col_u2, col_u3 = st.columns([0.5, 0.3, 0.2])
        col_u1.write(f"👤 **{u['nombre']}**")
        col_u2.write(f"🏷️ _{u['rol']}_")
        if "Administrador" not in u['rol']:
            if col_u3.button("🗑️ Eliminar", key=f"del_{i}"):
                st.session_state["users"].pop(i)
                st.success("Usuario eliminado con éxito.")
                st.rerun()

# --- SOLAPA 4: COMPARTIR APLICACIÓN ---
elif menu == "🌐 Compartir Aplicación":
    st.header("🌐 Enlace de Acceso en Línea")
    st.write("Para que cualquier persona pueda descargar y usar esta aplicación en línea desde su celular o computadora, sigue los pasos de despliegue gratuito detallados abajo:")
    
    st.markdown("""
    ### Pasos para habilitar el link público:
    1. Sube los archivos de tu aplicación (`aplicación.py`, `datos.py`, `clima.py` y un archivo `requirements.txt` con las librerías `streamlit`, `requests`, `fpdf`) a un repositorio público en **GitHub**.
    2. Ingresa a **[Streamlit Community Cloud](https://share.streamlit.io/)** e inicia sesión con tu cuenta de GitHub.
    3. Haz clic en **New app**, selecciona tu repositorio y el archivo principal (`aplicación.py`).
    4. Haz clic en **Deploy** y obtendrás automáticamente un enlace web personalizado (ejemplo: `https://tu-app-caba.streamlit.app`).
    """)
    
    st.markdown("---")
    st.info("🔗 **Link de ejemplo para compartir:** \n`https://sppro-caba-operativo.streamlit.app`")
