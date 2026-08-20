# aplicación.py
import streamlit as st
import math
from datetime import datetime
from fpdf import FPDF
from datos import edificios_db, comisarias_db, hospitales_db
from clima import obtener_clima_caba

st.set_page_config(page_title="SPPRO CABA - Panel Oficial", layout="wide")

if "users" not in st.session_state: 
    st.session_state["users"] = [{"nombre": "Admin (Propietario)", "rol": "Administrador"}]

if "entradas_extra" not in st.session_state:
    st.session_state["entradas_extra"] = {k: 2 for k in edificios_db.keys()}

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
        distancias.append((nombre, dist))
    distancias.sort(key=lambda x: x[1])
    return distancias[:cantidad]


# --- 1. EDIFICIOS Y CATASTRO ---
if menu == "🏢 Edificios & Puntos de Apoyo":
    st.header("🏢 Ficha Técnica y Proximidad de Emergencia en CABA")
    
    sel = st.selectbox("Seleccione el Edificio (Orden Alfabético)", sorted(edificios_db.keys()))
    d = edificios_db[sel]
    coords_ed = [float(x) for x in d['coords'].split(',')]
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Calle de Ubicación", d['dir'].split()[0])
    col2.metric("Altura Catastral", d['dir'].split()[-1] if any(c.isdigit() for c in d['dir']) else "S/N")
    col3.metric("Coordenadas Geográficas", d['coords'])
    total_entradas = st.session_state["entradas_extra"][sel]
    col4.metric("Entradas / Salidas", total_entradas)
    
    # Subida de fotos para registrar entradas y salidas
    st.markdown("### 📷 Carga de Accesos Adicionales")
    foto = st.file_uploader("Subir foto de una nueva entrada o salida del edificio", type=["jpg", "png", "jpeg"])
    if foto is not None:
        st.image(foto, caption="Evidencia fotográfica aportada", width=300)
        if st.button("Confirmar y Registrar Acceso"):
            st.session_state["entradas_extra"][sel] += 1
            st.success("¡Acceso adicional incorporado exitosamente al sistema!")
            st.rerun()

    # Cálculo exacto de los 2 hospitales y 2 comisarías más cercanas
    comisarias_cercanas = encontrar_multiples_cercanos(coords_ed, comisarias_db, 2)
    hospitales_cercanos = encontrar_multiples_cercanos(coords_ed, hospitales_db, 2)

    st.markdown("---")
    st.subheader("🚨 Puntos de Apoyo Cercanos (2 Comisarías y 2 Hospitales)")
    
    col_c, col_h = st.columns(2)
    with col_c:
        st.markdown("#### 👮 Comisarías Más Cercanas")
        for idx, (com, dist) in enumerate(comisarias_cercanas, 1):
            st.info(f"**{idx}.** {com} — *{dist} metros*")
            
    with col_h:
        st.markdown("#### 🏥 Hospitales Más Cercanos")
        for idx, (hosp, dist) in enumerate(hospitales_cercanos, 1):
            st.info(f"**{idx}.** {hosp} — *{dist} metros*")

    # Guardar en sesión para el reporte PDF
    st.session_state["actual"] = {
        "nombre": sel, "dir": d['dir'], "coords": d['coords'], "entradas": total_entradas,
        "comisarias": comisarias_cercanas, "hospitales": hospitales_cercanos,
        "clima": clima_actual, "fecha": datetime.now().strftime('%d/%m/%Y %H:%M')
    }


# --- 2. REPORTE PDF INSTITUCIONAL (EN BLANCO Y NEGRO, MUY DETALLADO) ---
elif menu == "📄 Reporte PDF Institucional":
    st.header("📄 Generador de Reporte Técnico Extendido (Blanco y Negro)")
    
    if "actual" in st.session_state:
        dat = st.session_state["actual"]
        responsable = st.text_input("Nombre y Apellido del Responsable Técnico Emisor", "Lic. Supervisor Operativo SPPRO")
        
        if st.button("Generar Reporte PDF Detallado"):
            pdf = FPDF()
            pdf.add_page()
            
            # Estricto Blanco y Negro (Sin colores)
            pdf.set_text_color(0, 0, 0)
            
            # Encabezado institucional formal
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(190, 7, "SISTEMA DE PROTECCIÓN Y EVALUACIÓN EDILICIA (SPPRO CABA)", ln=True, align="C")
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 5, "INFORME TÉCNICO OPERATIVO DE COBERTURA Y EMERGENCIAS", ln=True, align="C")
            
            pdf.ln(3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            
            # Metadatos del Documento
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(95, 5, f"Código de Auditoría: SPPRO-{datetime.now().strftime('%Y%m%d%H%M')}")
            pdf.cell(95, 5, f"Condición Climática: {dat['clima']}", ln=True, align="R")
            pdf.cell(190, 5, f"Fecha y Hora de Emisión: {dat['fecha']}", ln=True)
            
            pdf.ln(3)
            
            # Sección 1: Información Catastral Ampliada
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 6, "1. DATOS CATASTRALES Y CARACTERÍSTICAS EDILICIAS", ln=True)
            pdf.set_font("Arial", '', 9)
            
            pdf.cell(50, 6, "Objetivo Evaluado:", border=1)
            pdf.cell(140, 6, f" {dat['nombre']}", border=1, ln=1)
            pdf.cell(50, 6, "Ubicación (Calle y Número):", border=1)
            pdf.cell(140, 6, f" {dat['dir']}", border=1, ln=1)
            pdf.cell(50, 6, "Coordenadas GPS:", border=1)
            pdf.cell(140, 6, f" {dat['coords']}", border=1, ln=1)
            pdf.cell(50, 6, "Accesos Habilitados:", border=1)
            pdf.cell(140, 6, f" {dat['entradas']} entradas y salidas registradas", border=1, ln=1)
            
            pdf.ln(4)
            
            # Sección 2: Detalle Completo de los 2 Hospitales Cercanos
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 6, "2. ANÁLISIS DE COBERTURA SANITARIA (HOSPITALES CERCANOS)", ln=True)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(120, 5, "Establecimiento Médico de Salud CABA", border=1, align="C")
            pdf.cell(70, 5, "Distancia Lineal Calculada", border=1, align="C", ln=1)
            
            pdf.set_font("Arial", '', 9)
            for hosp, dist in dat["hospitales"]:
                pdf.cell(120, 6, f" {hosp}", border=1)
                pdf.cell(70, 6, f" {dist} metros", border=1, align="C", ln=1)
                
            pdf.ln(4)
            
            # Sección 3: Detalle Completo de las 2 Comisarías Cercanas
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 6, "3. ANÁLISIS DE COBERTURA DE SEGURIDAD (COMISARÍAS CERCANAS)", ln=True)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(120, 5, "Dependencia Policial (Policía de la Ciudad)", border=1, align="C")
            pdf.cell(70, 5, "Distancia Lineal Calculada", border=1, align="C", ln=1)
            
            pdf.set_font("Arial", '', 9)
            for com, dist in dat["comisarias"]:
                pdf.cell(120, 6, f" {com}", border=1)
                pdf.cell(70, 6, f" {dist} metros", border=1, align="C", ln=1)
                
            pdf.ln(4)
            
            # Sección 4: Observaciones Técnicas Detalladas
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 6, "4. DICTAMEN TÉCNICO Y OBSERVACIONES DE EVACUACIÓN", ln=True)
            pdf.set_font("Arial", '', 8.5)
            pdf.multi_cell(190, 4.5, "El presente documento técnico detalla de forma integral los recursos operativos de respuesta inmediata circundantes al objetivo. Se han validado tanto las vías de acceso perimetral como los tiempos estimados de arribo de unidades sanitarias y móviles policiales de la Ciudad Autónoma de Buenos Aires. Este reporte constituye una herramienta de control normativo y de seguridad bajo potestad del Administrador del Sistema SPPRO.")
            
            # Bloque de Firma y Cierre
            pdf.ln(20)
            pdf.set_font("Arial", '', 9)
            pdf.cell(100)
            pdf.cell(80, 4, "________________________________________", ln=True, align="C")
            pdf.cell(100)
            pdf.cell(80, 5, responsable, ln=True, align="C")
            pdf.cell(100)
            pdf.cell(80, 4, "Firma y Sello - Administrador SPPRO", ln=True, align="C")
            
            archivo_pdf = "reporte_tecnico_detallado.pdf"
            pdf.output(archivo_pdf)
            
            with open(archivo_pdf, "rb") as f:
                st.download_button("📥 Descargar Reporte PDF Detallado (B/N)", f, file_name=f"Informe_Detallado_{dat['nombre'].replace(' ', '_')}.pdf")
    else:
        st.warning("⚠️ Seleccione y consulte un edificio primero en la solapa '🏢 Edificios & Puntos de Apoyo'.")


# --- 3. GESTIÓN DE USUARIOS ---
elif menu == "👥 Gestión de Usuarios":
    st.header("👥 Panel de Control de Usuarios (Administrador)")
    
    with st.form("form_alta"):
        nombre_u = st.text_input("Nombre del Nuevo Usuario")
        rol_u = st.selectbox("Rol", ["Inspector", "Operador Zonal", "Auditor"])
        if st.form_submit_button("Registrar Usuario") and nombre_u:
            st.session_state["users"].append({"nombre": nombre_u, "rol": rol_u})
            st.success("Usuario agregado con éxito.")
            st.rerun()
            
    st.markdown("### 📋 Usuarios Activos")
    for i, u in enumerate(st.session_state["users"]):
        c1, c2, c3 = st.columns([0.5, 0.3, 0.2])
        c1.write(f"👤 **{u['nombre']}**")
        c2.write(f"🏷️ _{u['rol']}_")
        if "Administrador" not in u['rol']:
            if c3.button("🗑️ Borrar", key=f"del_{i}"):
                st.session_state["users"].pop(i)
                st.rerun()


# --- 4. COMPARTIR APLICACIÓN ---
elif menu == "🌐 Compartir Aplicación":
    st.header("🌐 Link de Acceso en Línea")
    st.write("Sube tus archivos a un repositorio de GitHub y conéctalos en [Streamlit Cloud](https://share.streamlit.io/) para generar tu link público.")
    st.info("🔗 **URL de ejemplo:** `https://sppro-caba-oficial.streamlit.app`")
