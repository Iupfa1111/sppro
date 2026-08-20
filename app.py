from datetime import datetime
import os
import sqlite3
from fpdf import FPDF
import requests
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SPPRO - Seguridad Patrimonial",
    layout="wide",
    page_icon="🛡️",
)

# --- BASE DE DATOS Y DATOS REALES ---


def init_db():
  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()

  # Tablas
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS edificios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            direccion TEXT,
            altura TEXT,
            accesos TEXT,
            coords TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            activo BOOLEAN
        )
    """)

  # 30 Edificios Emblemáticos de CABA con datos reales
  cursor.execute("SELECT COUNT(*) FROM edificios")
  if cursor.fetchone()[0] == 0:
    edificios_30 = [
        (
            "Edificio Kavanagh",
            "Florida 1065, Retiro",
            "120 m",
            "Acceso Principal / Cocheras",
            "-34.5922, -58.3753",
        ),
        (
            "Palacio Barolo",
            "Av. de Mayo 1370, Monserrat",
            "100 m",
            "Acceso Principal / Carga",
            "-34.6095, -58.3860",
        ),
        (
            "Teatro Colón",
            "Cerrito 628, San Nicolás",
            "30 m",
            "Varios (Calle Libertad / Tucumán)",
            "-34.6011, -58.3816",
        ),
        (
            "Congreso de la Nación Argentina",
            "Av. Entre Ríos 50, Balvanera",
            "80 m",
            "Entrada Principal / Protocolar",
            "-34.6099, -58.3916",
        ),
        (
            "Casa Rosada",
            "Balcarce 50, Monserrat",
            "24 m",
            "Balcarce 24 / Explanada",
            "-34.6081, -58.3702",
        ),
        (
            "Edificio Libertador (Min. de Defensa)",
            "Azopardo 250, Monserrat",
            "45 m",
            "Azopardo / Paseo Colón",
            "-34.6118, -58.3695",
        ),
        (
            "Edificio Centinela (Gendarmería Nacional)",
            "Av. Antártida Argentina 1480, Retiro",
            "40 m",
            "Acceso General",
            "-34.5885, -58.3731",
        ),
        (
            "Edificio Cóndor (Fuerza Aérea)",
            "Comodoro Py 2055, Retiro",
            "35 m",
            "Comodoro Py",
            "-34.5862, -58.3694",
        ),
        (
            "Catedral Metropolitana",
            "San Martín 27, San Nicolás",
            "25 m",
            "Acceso Frontal",
            "-34.6075, -58.3737",
        ),
        (
            "Cabildo de Buenos Aires",
            "Bolívar 65, Monserrat",
            "20 m",
            "Acceso Principal",
            "-34.6084, -58.3732",
        ),
        (
            "Palacio de Justicia (Tribunales)",
            "Talcahuano 550, San Nicolás",
            "50 m",
            "Talcahuano / Lavalle",
            "-34.6033, -58.3872",
        ),
        (
            "Facultad de Derecho UBA",
            "Av. Figueroa Alcorta 2263, Recoleta",
            "35 m",
            "Escinata Principal / Figueroa Alcorta",
            "-34.5833, -58.3897",
        ),
        (
            "Biblioteca Nacional",
            "Agüero 2502, Recoleta",
            "40 m",
            "Agüero / Las Heras",
            "-34.5847, -58.4011",
        ),
        (
            "Galerías Pacífico",
            "Av. Florida 737, San Nicolás",
            "25 m",
            "Florida / Viamonte / Córdoba",
            "-34.5997, -58.3744",
        ),
        (
            "CCK (Centro Cultural Kirchner)",
            "Sarmiento 151, Monserrat",
            "40 m",
            "Sarmiento / Leandro N. Alem",
            "-34.6044, -58.3694",
        ),
        (
            "Hotel Alvear",
            "Av. Alvear 1891, Recoleta",
            "50 m",
            "Av. Alvear / Ayacucho",
            "-34.5883, -58.3881",
        ),
        (
            "Estación Retiro Mitre",
            "Av. Dr. Ramos Mejía 1302, Retiro",
            "30 m",
            "Hall Central / Andenes",
            "-34.5903, -58.3742",
        ),
        (
            "Estación Constitución",
            "Av. Brasil 1152, Constitución",
            "30 m",
            "Hall Principal / Brasil",
            "-34.6281, -58.3814",
        ),
        (
            "Estación Once",
            "Av. Pueyrredón 1855, Balvanera",
            "25 m",
            "Pueyrredón / Mitre",
            "-34.6095, -58.4078",
        ),
        (
            "Banco de la Nación Argentina",
            "Rivadavia 325, Monserrat",
            "40 m",
            "Rivadavia / Bartolomé Mitre",
            "-34.6083, -58.3721",
        ),
        (
            "Bolsa de Comercio de Buenos Aires",
            "25 de Mayo 359, San Nicolás",
            "35 m",
            "25 de Mayo / Sarmiento",
            "-34.6053, -58.3736",
        ),
        (
            "Club Gimnasia y Esgrima BA",
            "Bmé. Mitre 1149, San Nicolás",
            "20 m",
            "Acceso Principal",
            "-34.6042, -58.3831",
        ),
        (
            "Círculo Militar (Palacio Paz)",
            "Av. Santa Fe 750, Retiro",
            "45 m",
            "Av. Santa Fe / Maipú",
            "-34.5947, -58.3789",
        ),
        (
            "Usina del Arte",
            "Agustín Caffarena 1, La Boca",
            "25 m",
            "Caffarena / Don Pedro de Mendoza",
            "-34.6342, -58.3639",
        ),
        (
            "Museo Nacional de Bellas Artes",
            "Av. Del Libertador 1473, Recoleta",
            "20 m",
            "Libertador",
            "-34.5853, -58.3931",
        ),
        (
            "Hospital de Clínicas José de San Martín",
            "Av. Córdoba 2351, Recoleta",
            "45 m",
            "Av. Córdoba / Paraguay",
            "-34.5983, -58.3986",
        ),
        (
            "Legislatura de la Ciudad de Buenos Aires",
            "Peru 160, Monserrat",
            "35 m",
            "Perú / Julio A. Roca",
            "-34.6091, -58.3751",
        ),
        (
            "Jefatura de Gobierno CABA (Parque Patricios)",
            "Uspallata 3160, Parque Patricios",
            "30 m",
            "Uspallata / Los Patos",
            "-34.6386, -58.4069",
        ),
        (
            "Torre Madero",
            "Av. Eduardo Madero 1020, Puerto Madero",
            "100 m",
            "Madero / Bouchard",
            "-34.5978, -58.3703",
        ),
        (
            "YPF Torre",
            "Macacha Güemes 515, Puerto Madero",
            "160 m",
            "Macacha Güemes / Dique 4",
            "-34.6031, -58.3639",
        ),
    ]
    cursor.executemany(
        "INSERT INTO edificios (nombre, direccion, altura, accesos, coords)"
        " VALUES (?, ?, ?, ?, ?)",
        edificios_30,
    )

  # Precargar usuarios iniciales si está vacía
  cursor.execute("SELECT COUNT(*) FROM usuarios")
  if cursor.fetchone()[0] == 0:
    usuarios_iniciales = [("admin_principal", True), ("operador_turno_1", True)]
    cursor.executemany(
        "INSERT INTO usuarios (username, activo) VALUES (?, ?)",
        usuarios_iniciales,
    )

  conn.commit()
  conn.close()


init_db()

# --- FUNCIONES DE APOYO ---


def obtener_clima():
  try:
    url = (
        "https://api.open-meteo.com/v1/forecast?latitude=-34.61&longitude=-58.37&current=temperature_2m,weather_code"
    )
    data = requests.get(url, timeout=5).json()
    temp = data["current"]["temperature_2m"]
    return f"{temp}°C (CABA)"
  except:
    return "No disponible"


def generar_pdf_ficha(nombre, dir_edif, alt_edif, acc_edif, coords_edif):
  pdf = FPDF()
  pdf.add_page()

  # Encabezado institucional
  pdf.set_font("Arial", "B", 16)
  pdf.set_text_color(20, 40, 80)
  pdf.cell(
      200, 10, txt="SPPRO - REPORTE DE VERIFICACIÓN PATRIMONIAL", ln=True, align="C"
  )

  pdf.set_font("Arial", "", 10)
  pdf.set_text_color(100, 100, 100)
  pdf.cell(
      200,
      6,
      txt=f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
      ln=True,
      align="C",
  )
  pdf.ln(10)

  # Datos del Edificio
  pdf.set_font("Arial", "B", 12)
  pdf.set_text_color(0, 0, 0)
  pdf.cell(200, 8, txt=f"Ficha Técnica: {nombre}", ln=True)

  pdf.set_font("Arial", "", 11)
  pdf.set_fill_color(240, 240, 240)
  pdf.cell(
      200, 8, txt=f"  Dirección: {dir_edif}", ln=True, fill=True
  )
  pdf.cell(
      200, 8, txt=f"  Altura Catastral: {alt_edif}", ln=True, fill=True
  )
  pdf.cell(
      200, 8, txt=f"  Entradas y Salidas: {acc_edif}", ln=True, fill=True
  )
  pdf.cell(
      200, 8, txt=f"  Coordenadas GPS: {coords_edif}", ln=True, fill=True
  )
  pdf.ln(10)

  # Puntos Seguros Asociados
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

  archivo_salida = f"reporte_{nombre.replace(' ', '_').lower()}.pdf"
  pdf.output(archivo_salida)
  return archivo_salida


# --- NAVEGACIÓN LATERAL (SOLAPAS) ---
with st.sidebar:
  st.title("🛡️ SPPRO v2.5")
  st.markdown("Sistema de Seguridad Patrimonial")
  st.divider()
  seleccion = st.radio(
      "Menú Principal",
      [
          "1️⃣ Verificación de Edificios",
          "2️⃣ Generación de PDF",
          "3️⃣ Administrador de Usuarios",
      ],
  )
  st.divider()
  st.caption("Estado del Sistema: 🟢 Operativo")

# ==========================================
# SOLAPA 1: VERIFICACIÓN DE EDIFICIOS
# ==========================================
if seleccion == "1️⃣ Verificación de Edificios":
  st.header("🏢 Módulo de Verificación de Edificios")

  # Métrica de clima en tiempo real
  st.metric(
      label="Condiciones Climáticas Actuales", value=obtener_clima()
  )
  st.markdown("---")

  # Conexión DB para listar
  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()
  cursor.execute("SELECT nombre FROM edificios")
  nombres_edificios = [r[0] for r in cursor.fetchall()]
  conn.close()

  # Botones de selección / edición
  tipo_accion = st.radio(
      "Seleccione una opción:",
      [
          "📋 Listado de los 30 Edificios Emblemáticos CABA",
          "➕ Ingresar / Editar Edificio Nuevo",
      ],
      horizontal=True,
  )

  edificio_elegido = None

  if tipo_accion.startswith("📋"):
    edificio_elegido = st.selectbox(
        "Seleccione el edificio emblemático:", nombres_edificios
    )
  else:
    with st.form("form_nuevo"):
      st.subheader("Registro de Nuevo Edificio")
      n_nombre = st.text_input("Nombre del Edificio")
      n_dir = st.text_input("Dirección Exacta")
      n_alt = st.text_input("Altura Catastral (Ej. 45 m)")
      n_acc = st.text_input("Entradas y Salidas (Ej. Principal / Cochera)")
      n_coord = st.text_input("Coordenadas GPS (Ej. -34.60, -58.38)")
      submit_nuevo = st.form_submit_button("Guardar Edificio")

      if submit_nuevo and n_nombre:
        try:
          conn = sqlite3.connect("sppro.db")
          cursor = conn.cursor()
          cursor.execute(
              "INSERT OR REPLACE INTO edificios (nombre, direccion, altura,"
              " accesos, coords) VALUES (?, ?, ?, ?, ?)",
              (n_nombre, n_dir, n_alt, n_acc, n_coord),
          )
          conn.commit()
          conn.close()
          st.success(
              f"Edificio '{n_nombre}' guardado exitosamente. Ya puede"
              " seleccionarlo."
          )
          edificio_elegido = n_nombre
        except Exception as e:
          st.error(f"Error al registrar: {e}")

  st.markdown("---")

  if st.button("🔍 VERIFICAR EDIFICIO", type="primary"):
    if edificio_elegido:
      conn = sqlite3.connect("sppro.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT direccion, altura, accesos, coords FROM edificios WHERE"
          " nombre = ?",
          (edificio_elegido,),
      )
      info = cursor.fetchone()
      conn.close()

      if info:
        st.session_state["active_edificio"] = edificio_elegido
        st.session_state["active_info"] = info

  # Mostrar ficha técnica si se presionó verificar
  if "active_edificio" in st.session_state:
    nom = st.session_state["active_edificio"]
    d, a, ac, c = st.session_state["active_info"]

    st.success(f"Ficha Técnica Activa: **{nom}**")

    col1, col2 = st.columns(2)
    with col1:
      st.info(f"📍 **Dirección:** {d}")
      st.info(f"📏 **Altura Catastral:** {a}")
    with col2:
      st.info(f"🚪 **Entradas/Salidas:** {ac}")
      st.info(f"🌐 **Coordenadas:** {c}")

    st.markdown("### 📷 Carga de Fotografías / Evidencia")
    st.file_uploader(
        (
            "Adjuntar registros fotográficos para futuros eventos o bitácoras"
            " patrimoniales"
        ),
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    st.markdown("### 🛡️ Puntos Seguros Cercanos (CABA)")
    st.write(
        "🏥 **Hospital General de Agudos J. A. Fernández** — Cerviño 3356,"
        " Recoleta"
    )
    st.write("🚨 **Comisaría Vecinal 1A** — Suipacha 1156, Retiro")
    st.write(
        "🏛️ **Departamento Central de Policía (PFA)** — Av. Cnel. Díaz 1850,"
        " Palermo"
    )
    st.write(
        "⭐ **Edificio Libertador (Min. de Defensa / FFAA)** — Azopardo 250,"
        " Monserrat"
    )

# ==========================================
# SOLAPA 2: GENERACIÓN DE PDF
# ==========================================
elif seleccion == "2️⃣ Generación de PDF":
  st.header("📄 Generación de Reportes PDF")
  st.markdown(
      "Exporte la ficha técnica y los puntos de control en un formato PDF"
      " formal, limpio y profesional."
  )

  if "active_edificio" in st.session_state:
    nom = st.session_state["active_edificio"]
    d, a, ac, c = st.session_state["active_info"]

    st.info(
        "Edificio listo para exportar: **"
        + nom
        + "**\n\nHaga clic en el botón inferior para compilar el documento."
    )

    if st.button("📥 Generar y Descargar PDF Institucional", type="primary"):
      archivo_generado = generar_pdf_ficha(nom, d, a, ac, c)
      with open(archivo_generado, "rb") as f:
        st.download_button(
            label="💾 Descargar Archivo PDF Ahora",
            data=f,
            file_name=archivo_generado,
            mime="application/pdf",
        )
      st.success("¡PDF generado correctamente!")
  else:
    st.warning(
        "⚠️ Atención: Primero debe seleccionar y verificar un edificio en la"
        " solapa **Verificación de Edificios**."
    )

# ==========================================
# SOLAPA 3: ADMINISTRADOR DE USUARIOS
# ==========================================
elif seleccion == "3️⃣ Administrador de Usuarios":
  st.header("👤 Panel de Administración de Usuarios")
  st.markdown(
      "Control de accesos del personal. Habilite o deshabilite cuentas de"
      " forma inmediata por razones de seguridad operativa."
  )

  conn = sqlite3.connect("sppro.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, username, activo FROM usuarios")
  usuarios = cursor.fetchall()

  st.subheader("Operadores Registrados")
  for uid, uname, uact in usuarios:
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
      st.text(f"👤 {uname}")
    with c2:
      st.markdown(
          "🟢 **Habilitado**" if uact else "🔴 **Deshabilitado**",
          unsafe_allow_html=True,
      )
    with c3:
      nuevo_estado = not uact
      etiqueta = "Deshabilitar" if uact else "Habilitar"
      if st.button(etiqueta, key=f"user_btn_{uid}"):
        cursor.execute(
            "UPDATE usuarios SET activo = ? WHERE id = ?", (nuevo_estado, uid)
        )
        conn.commit()
        st.rerun()

  st.divider()
  st.subheader("Registrar Nuevo Operador")
  with st.form("nuevo_usuario"):
    nuevo_nombre = st.text_input("Nombre de Usuario / Legajo")
    crear_btn = st.form_submit_button("Dar de Alta")
    if crear_btn and nuevo_nombre:
      try:
        cursor.execute(
            "INSERT INTO usuarios (username, activo) VALUES (?, ?)",
            (nuevo_nombre, True),
        )
        conn.commit()
        st.success(f"Usuario {nuevo_nombre} creado correctamente.")
        st.rerun()
      except Exception as e:
        st.error(f"No se pudo crear el usuario (posible nombre duplicado): {e}")

  conn.close()
