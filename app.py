from datetime import datetime
from fpdf import FPDF
import requests
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SPPRO - Seguridad Patrimonial",
    layout="wide",
    page_icon="🛡️",
)

# --- LISTA COMPLETA DE LOS 30 EDIFICIOS EMBLEMÁTICOS DE CABA ---
lista_edificios = {
    "Edificio Kavanagh": {
        "dir": "Florida 1065, Retiro",
        "alt": "120 m",
        "acc": "Acceso Principal / Cocheras",
        "coords": "-34.5922, -58.3753",
    },
    "Palacio Barolo": {
        "dir": "Av. de Mayo 1370, Monserrat",
        "alt": "100 m",
        "acc": "Acceso Principal / Carga",
        "coords": "-34.6095, -58.3860",
    },
    "Teatro Colón": {
        "dir": "Cerrito 628, San Nicolás",
        "alt": "30 m",
        "acc": "Libertad / Tucumán",
        "coords": "-34.6011, -58.3816",
    },
    "Congreso de la Nación Argentina": {
        "dir": "Av. Entre Ríos 50, Balvanera",
        "alt": "80 m",
        "acc": "Principal / Protocolar",
        "coords": "-34.6099, -58.3916",
    },
    "Casa Rosada": {
        "dir": "Balcarce 50, Monserrat",
        "alt": "24 m",
        "acc": "Balcarce 24 / Explanada",
        "coords": "-34.6081, -58.3702",
    },
    "Edificio Libertador (Min. de Defensa)": {
        "dir": "Azopardo 250, Monserrat",
        "alt": "45 m",
        "acc": "Azopardo / Paseo Colón",
        "coords": "-34.6118, -58.3695",
    },
    "Edificio Centinela (Gendarmería)": {
        "dir": "Av. Antártida Argentina 1480, Retiro",
        "alt": "40 m",
        "acc": "Acceso General",
        "coords": "-34.5885, -58.3731",
    },
    "Edificio Cóndor (Fuerza Aérea)": {
        "dir": "Comodoro Py 2055, Retiro",
        "alt": "35 m",
        "acc": "Comodoro Py",
        "coords": "-34.5862, -58.3694",
    },
    "Catedral Metropolitana": {
        "dir": "San Martín 27, San Nicolás",
        "alt": "25 m",
        "acc": "Acceso Frontal",
        "coords": "-34.6075, -58.3737",
    },
    "Cabildo de Buenos Aires": {
        "dir": "Bolívar 65, Monserrat",
        "alt": "20 m",
        "acc": "Acceso Principal",
        "coords": "-34.6084, -58.3732",
    },
    "Palacio de Justicia (Tribunales)": {
        "dir": "Talcahuano 550, San Nicolás",
        "alt": "50 m",
        "acc": "Talcahuano / Lavalle",
        "coords": "-34.6033, -58.3872",
    },
    "Facultad de Derecho UBA": {
        "dir": "Av. Figueroa Alcorta 2263, Recoleta",
        "alt": "35 m",
        "acc": "Escinata Principal",
        "coords": "-34.5833, -58.3897",
    },
    "Biblioteca Nacional": {
        "dir": "Agüero 2502, Recoleta",
        "alt": "40 m",
        "acc": "Agüero / Las Heras",
        "coords": "-34.5847, -58.4011",
    },
    "Galerías Pacífico": {
        "dir": "Av. Florida 737, San Nicolás",
        "alt": "25 m",
        "acc": "Florida / Viamonte",
        "coords": "-34.5997, -58.3744",
    },
    "CCK (Centro Cultural Kirchner)": {
        "dir": "Sarmiento 151, Monserrat",
        "alt": "40 m",
        "acc": "Sarmiento / Alem",
        "coords": "-34.6044, -58.3694",
    },
    "Hotel Alvear": {
        "dir": "Av. Alvear 1891, Recoleta",
        "alt": "50 m",
        "acc": "Av. Alvear / Ayacucho",
        "coords": "-34.5883, -58.3881",
    },
    "Estación Retiro Mitre": {
        "dir": "Av. Dr. Ramos Mejía 1302, Retiro",
        "alt": "30 m",
        "acc": "Hall Central / Andenes",
        "coords": "-34.5903, -58.3742",
    },
    "Estación Constitución": {
        "dir": "Av. Brasil 1152, Constitución",
        "alt": "30 m",
        "acc": "Hall Principal / Brasil",
        "coords": "-34.6281, -58.3814",
    },
    "Estación Once": {
        "dir": "Av. Pueyrredón 1855, Balvanera",
        "alt": "25 m",
        "acc": "Pueyrredón / Mitre",
        "coords": "-34.6095, -58.4078",
    },
    "Banco de la Nación Argentina": {
        "dir": "Rivadavia 325, Monserrat",
        "alt": "40 m",
        "acc": "Rivadavia / Mitre",
        "coords": "-34.6083, -58.3721",
    },
    "Bolsa de Comercio de Buenos Aires": {
        "dir": "25 de Mayo 359, San Nicolás",
        "alt": "35 m",
        "acc": "25 de Mayo / Sarmiento",
        "coords": "-34.6053, -58.3736",
    },
    "Club Gimnasia y Esgrima BA": {
        "dir": "Bmé. Mitre 1149, San Nicolás",
        "alt": "20 m",
        "acc": "Acceso Principal",
        "coords": "-34.6042, -58.3831",
    },
    "Círculo Militar (Palacio Paz)": {
        "dir": "Av. Santa Fe 750, Retiro",
        "alt": "45 m",
        "acc": "Santa Fe / Maipú",
        "coords": "-34.5947, -58.3789",
    },
    "Usina del Arte": {
        "dir": "Agustín Caffarena 1, La Boca",
        "alt": "25 m",
        "acc": "Caffarena / Don Pedro",
        "coords": "-34.6342, -58.3639",
    },
    "Museo Nacional de Bellas Artes": {
        "dir": "Av. Del Libertador 1473, Recoleta",
        "alt": "20 m",
        "acc": "Libertador",
        "coords": "-34.5853, -58.3931",
    },
    "Hospital de Clínicas": {
        "dir": "Av. Córdoba 2351, Recoleta",
        "alt": "45 m",
        "acc": "Av. Córdoba / Paraguay",
        "coords": "-34.5983, -58.3986",
    },
    "Legislatura de la Ciudad de Buenos Aires": {
        "dir": "Peru 160, Monserrat",
        "alt": "35 m",
        "acc": "Perú / Julio A. Roca",
        "coords": "-34.6091, -58.3751",
    },
    "Jefatura de Gobierno CABA": {
        "dir": "Uspallata 3160, Parque Patricios",
        "alt": "30 m",
        "acc": "Uspallata / Los Patos",
        "coords": "-34.6386, -58.4069",
    },
    "Torre Madero": {
        "dir": "Av. Eduardo Madero 1020, Puerto Madero",
        "alt": "100 m",
        "acc": "Madero / Bouchard",
        "coords": "-34.5978, -58.3703",
    },
    "YPF Torre": {
        "dir": "Macacha Güemes 515, Puerto Madero",
        "alt": "160 m",
        "acc": "Macacha Güemes / Dique 4",
        "coords": "-34.6031, -58.3639",
    },
}

# --- NAVEGACIÓN LATERAL (SOLAPAS) ---
with st.sidebar:
  st.title("🛡️ SPPRO v3.0")
  st.markdown("Seguridad Patrimonial CABA")
  st.divider()
  menu = st.radio(
      "Navegación",
      [
          "1️⃣ Verificación de Edificios",
          "2️⃣ Generación de PDF",
          "3️⃣ Administrador de Usuarios",
      ],
  )
  st.divider()
  st.caption("Estado: 🟢 En Línea")

# ==========================================
# SOLAPA 1: VERIFICACIÓN DE EDIFICIOS
# ==========================================
if menu == "1️⃣ Verificación de Edificios":
  st.header("🏢 Control y Verificación de Edificios")

  # Clima en tiempo real
  try:
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast?latitude=-34.61&longitude=-58.37&current=temperature_2m",
        timeout=3,
    )
    temp = r.json()["current"]["temperature_2m"]
    st.metric("🌡️ Clima Actual en CABA", f"{temp}°C")
  except:
    st.metric("🌡️ Clima Actual en CABA", "No disponible")

  st.divider()

  # Selección de edificio
  edificio_elegido = st.selectbox(
      "Seleccione un Edificio Emblemático de CABA", list(lista_edificios.keys())
  )

  if st.button("🔍 VERIFICAR EDIFICIO", type="primary"):
    info = lista_edificios[edificio_elegido]
    st.session_state["activo_nombre"] = edificio_elegido
    st.session_state["activo_datos"] = info

  # Mostrar ficha técnica si se presionó verificar
  if "activo_nombre" in st.session_state:
    nom = st.session_state["activo_nombre"]
    dat = st.session_state["activo_datos"]

    st.success(f"Ficha Técnica Activa: **{nom}**")

    col1, col2 = st.columns(2)
    with col1:
      st.markdown(f"**📍 Dirección:** {dat['dir']}")
      st.markdown(f"**📏 Altura Catastral:** {dat['alt']}")
    with col2:
      st.markdown(f"**🚪 Entradas y Salidas:** {dat['acc']}")
      st.markdown(f"**🌐 Coordenadas GPS:** {dat['coords']}")

    st.markdown("---")
    st.subheader("📷 Carga de Fotografías / Evidencia")
    st.file_uploader(
        (
            "Adjuntar registros fotográficos para futuros eventos o bitácoras"
            " patrimoniales"
        ),
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    st.markdown("---")
    st.subheader("🛡️ Puntos Seguros Cercanos (CABA)")
    st.info(
        "🏥 **Hospital General de Agudos J. A. Fernández** — Cerviño 3356,"
        " Recoleta"
    )
    st.info("🚨 **Comisaría Vecinal 1A** — Suipacha 1156, Retiro")
    st.info(
        "🏛️ **Departamento Central de Policía (PFA)** — Av. Cnel. Díaz 1850,"
        " Palermo"
    )
    st.info(
        "⭐ **Edificio Libertador (Min. de Defensa / FFAA)** — Azopardo 250,"
        " Monserrat"
    )

# ==========================================
# SOLAPA 2: GENERACIÓN DE PDF
# ==========================================
elif menu == "2️⃣ Generación de PDF":
  st.header("📄 Generador de Reportes PDF")
  st.markdown(
      "Exporte la ficha técnica y los puntos de control en un formato PDF"
      " formal, limpio y profesional."
  )

  if "activo_nombre" in st.session_state:
    nom = st.session_state["activo_nombre"]
    dat = st.session_state["activo_datos"]

    st.info(f"Edificio seleccionado para exportar: **{nom}**")

    if st.button("📥 Generar Archivo PDF Institucional", type="primary"):
      pdf = FPDF()
      pdf.add_page()

      # Encabezado
      pdf.set_font("Arial", "B", 16)
      pdf.set_text_color(20, 40, 80)
      pdf.cell(
          200,
          10,
          txt="SPPRO - REPORTE DE VERIFICACIÓN PATRIMONIAL",
          ln=True,
          align="C",
      )

      pdf.set_font("Arial", "", 10)
      pdf.set_text_color(100, 100, 100)
      pdf.cell(
          200,
          6,
          txt=(
              "Fecha de Emisión: "
              + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
          ),
          ln=True,
          align="C",
      )
      pdf.ln(10)

      # Datos
      pdf.set_font("Arial", "B", 12)
      pdf.set_text_color(0, 0, 0)
      pdf.cell(200, 8, txt=f"Ficha Técnica: {nom}", ln=True)

      pdf.set_font("Arial", "", 11)
      pdf.set_fill_color(240, 240, 240)
      pdf.cell(
          200, 8, txt=f"  Dirección: {dat['dir']}", ln=True, fill=True
      )
      pdf.cell(
          200, 8, txt=f"  Altura Catastral: {dat['alt']}", ln=True, fill=True
      )
      pdf.cell(
          200, 8, txt=f"  Entradas y Salidas: {dat['acc']}", ln=True, fill=True
      )
      pdf.cell(
          200, 8, txt=f"  Coordenadas GPS: {dat['coords']}", ln=True, fill=True
      )
      pdf.ln(10)

      # Puntos Seguros
      pdf.set_font("Arial", "B", 12)
      pdf.cell(200, 8, txt="Puntos Seguros de Referencia (CABA):", ln=True)
      pdf.set_font("Arial", "", 10)
      pdf.cell(
          200,
          6,
          txt=(
              "  - Hospital General de Agudos J. A. Fernández (Cerviño 3356,"
              " Recoleta)"
          ),
          ln=True,
      )
      pdf.cell(
          200,
          6,
          txt="  - Comisaría Vecinal 1A (Suipacha 1156, Retiro)",
          ln=True,
      )
      pdf.cell(
          200,
          6,
          txt=(
              "  - Departamento Central de Policía - PFA (Av. Cnel. Díaz 1850,"
              " Palermo)"
          ),
          ln=True,
      )
      pdf.cell(
          200,
          6,
          txt=(
              "  - Edificio Libertador - Min. de Defensa / FFAA (Azopardo 250,"
              " Monserrat)"
          ),
          ln=True,
      )

      archivo_salida = "reporte_edificio.pdf"
      pdf.output(archivo_salida)

      with open(archivo_salida, "rb") as f:
        st.download_button(
            label="💾 Descargar PDF en tu Dispositivo",
            data=f,
            file_name=archivo_salida,
            mime="application/pdf",
        )
      st.success("¡PDF generado correctamente!")
  else:
    st.warning(
        "⚠️ Atención: Primero debe seleccionar y verificar un edificio en la"
        " solapa **1️⃣ Verificación de Edificios**."
    )

# ==========================================
# SOLAPA 3: ADMINISTRADOR DE USUARIOS
# ==========================================
elif menu == "3️⃣ Administrador de Usuarios":
  st.header("👤 Panel de Administración de Usuarios")
  st.markdown(
      "Control de accesos del personal por razones de seguridad operativa."
  )

  st.text("👤 admin_principal — 🟢 Habilitado")
  st.text("👤 operador_turno_1 — 🟢 Habilitado")

  st.divider()
  st.subheader("Registrar Nuevo Operador")
  with st.form("nuevo_usuario"):
    nuevo_nombre = st.text_input("Nombre de Usuario / Legajo")
    crear_btn = st.form_submit_button("Dar de Alta")
    if crear_btn and nuevo_nombre:
      st.success(
          f"Usuario '{nuevo_nombre}' registrado temporalmente con éxito."
)
