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

# --- INICIALIZACIÓN DE ESTADOS EN MEMORIA ---
if "edificios_db" not in st.session_state:
  st.session_state["edificios_db"] = {
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

if "usuarios_db" not in st.session_state:
  st.session_state["usuarios_db"] = [
      "admin_principal",
      "operador_turno_1",
      "supervisor_general",
  ]

if "historial_auditoria" not in st.session_state:
  st.session_state["historial_auditoria"] = []


# --- FUNCIÓN DE CLIMA ---
def obtener_clima():
  try:
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast?latitude=-34.61&longitude=-58.37&current=temperature_2m",
        timeout=3,
    )
    temp = r.json()["current"]["temperature_2m"]
    return f"{temp} C"
  except:
    return "No disponible"


# Limpieza total blindada contra errores de codificación FPDF
def limpiar_texto(texto):
  if not isinstance(texto, str):
    texto = str(texto)

  reemplazos = {
      "á": "a",
      "é": "e",
      "í": "i",
      "ó": "o",
      "ú": "u",
      "Á": "A",
      "É": "E",
      "Í": "I",
      "Ó": "O",
      "Ú": "U",
      "ñ": "n",
      "Ñ": "N",
      "°": " deg",
      "—": "-",
      "–": "-",
      "“": '"',
      "”": '"',
      "‘": "'",
      "’": "'",
  }
  for k, v in reemplazos.items():
    texto = texto.replace(k, v)

  return (
      texto.encode("latin-1", errors="ignore")
      .decode("latin-1")
      .strip()
  )


# --- NAVEGACIÓN LATERAL ---
with st.sidebar:
  st.title("🛡️ SPPRO v3.6")
  st.markdown("Seguridad Patrimonial CABA")
  st.divider()
  menu = st.radio(
      "Navegacion",
      [
          "1️⃣ Verificacion de Edificios",
          "2️⃣ Generacion de PDF",
          "3️⃣ Auditoria y Reportes",
          "4️⃣ Administrador de Usuarios",
      ],
  )
  st.divider()
  st.caption("Estado: 🟢 En Línea")


# ==========================================
# SOLAPA 1: VERIFICACIÓN DE EDIFICIOS
# ==========================================
if menu == "1️⃣ Verificacion de Edificios":
  st.header("🏢 Control y Verificacion de Edificios")
  st.metric("🌡️ Clima Actual en CABA", obtener_clima())
  st.divider()

  with st.expander("➕ Agregar un Edificio Nuevo a la Base"):
    with st.form("nuevo_edificio_form"):
      n_nombre = st.text_input("Nombre del Edificio / Sitio")
      n_dir = st.text_input("Direccion Exacta")
      n_alt = st.text_input("Altura Catastral (Ej. 45 m)")
      n_acc = st.text_input("Entradas y Salidas (Ej. Principal / Carga)")
      n_coords = st.text_input("Coordenadas GPS (Ej. -34.60, -58.38)")
      btn_guardar_nuevo = st.form_submit_button("Guardar Nuevo Edificio")

      if btn_guardar_nuevo and n_nombre:
        st.session_state["edificios_db"][n_nombre] = {
            "dir": n_dir,
            "alt": n_alt,
            "acc": n_acc,
            "coords": n_coords,
        }
        st.success(f"Edificio '{n_nombre}' agregado correctamente.")

  st.divider()

  lista_nombres = list(st.session_state["edificios_db"].keys())
  edificio_elegido = st.selectbox(
      "Seleccionar Edificio / Sitio", lista_nombres
  )

  if st.button("🔍 VERIFICAR EDIFICIO", type="primary"):
    info = st.session_state["edificios_db"][edificio_elegido]
    st.session_state["activo_nombre"] = edificio_elegido
    st.session_state["activo_datos"] = info
    st.session_state["activo_clima"] = obtener_clima()
    st.session_state["fotos_cargadas"] = []

  if "activo_nombre" in st.session_state:
    nom = st.session_state["activo_nombre"]
    dat = st.session_state["activo_datos"]

    st.success(f"Ficha Tecnica Activa: **{nom}**")

    col1, col2 = st.columns(2)
    with col1:
      st.markdown(f"**📍 Dirección:** {dat['dir']}")
      st.markdown(f"**📏 Altura Catastral:** {dat['alt']}")
    with col2:
      st.markdown(f"**🚪 Entradas y Salidas:** {dat['acc']}")
      link_maps = f"https://www.google.com/maps/search/?api=1&query={dat['coords'].replace(' ', '')}"
      st.markdown(
          f"**🌐 Coordenadas GPS:** [{dat['coords']}]({link_maps}) *(Hacer clic"
          " para abrir en Google Maps)*",
          unsafe_allow_html=True,
      )

    st.markdown("---")
    st.subheader("📷 Carga y Previsualización de Evidencia Fotográfica")
    archivos_subidos = st.file_uploader(
        "Adjuntar registros fotográficos",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if archivos_subidos:
      st.session_state["fotos_cargadas"] = archivos_subidos
      st.markdown("### Previsualización de Evidencias Adjuntas:")
      cols_fotos = st.columns(len(archivos_subidos))
      for idx, foto in enumerate(archivos_subidos):
        with cols_fotos[idx]:
          st.image(
              foto,
              caption=f"Evidencia {idx+1}",
              use_container_width=True,
          )

    st.markdown("---")
    st.subheader("🛡️ Puntos Seguros Cercanos (CABA - Direcciones Reales)")
    st.info(
        "🏥 **Hospital General de Agudos J. A. Fernández** — Cerviño 3356,"
        " Recoleta"
    )
    st.info("🚨 **Comisaría Vecinal 1A** — Suipacha 1156, Retiro")
    st.info(
        "🏛️ **Departamento Central de Policía (PFA)** — Moreno 1550, Monserrat"
    )
    st.info(
        "⭐ **Edificio Libertador (Min. de Defensa / FFAA)** — Azopardo 250,"
        " Monserrat"
    )


# ==========================================
# SOLAPA 2: GENERACIÓN DE PDF
# ==========================================
elif menu == "2️⃣ Generacion de PDF":
  st.header("📄 Generador de Reportes PDF")
  st.markdown(
      "Diseño profesional institucional con tonos azules, clima y bloque de"
      " firma digital."
  )

  if "activo_nombre" in st.session_state:
    nom = st.session_state["activo_nombre"]
    dat = st.session_state["activo_datos"]
    clima_actual = st.session_state.get("activo_clima", "No registrado")

    st.info(f"Edificio listo para exportar: **{nom}**")

    firma_digital = st.text_input(
        "✍️ Ingrese el Nombre / Cargo para la Firma Digital",
        placeholder="Ej: Of. Juan Perez - Supervisor de Seguridad Patrimonial",
    )

    if st.button("📥 Generar PDF Institucional Profesional", type="primary"):
      pdf = FPDF()
      pdf.add_page()

      pdf.set_fill_color(24, 43, 73)
      pdf.rect(0, 0, 210, 25, "F")
      pdf.set_font("Arial", "B", 13)
      pdf.set_text_color(255, 255, 255)
      pdf.set_xy(10, 8)
      pdf.cell(
          190,
          10,
          txt=limpiar_texto("SPPRO - VERIFICACION DEL LUGAR DEL EVENTO"),
          ln=True,
          align="C",
      )

      pdf.ln(15)
      pdf.set_font("Arial", "", 9)
      pdf.set_text_color(100, 100, 100)
      fecha_hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
      pdf.cell(
          200,
          6,
          txt=limpiar_texto(f"Fecha y Hora de Emision: {fecha_hora_actual}"),
          ln=True,
          align="R",
      )
      pdf.cell(
          200,
          6,
          txt=limpiar_texto(
              f"Condiciones Climaticas al Momento: {clima_actual}"
          ),
          ln=True,
          align="R",
      )
      pdf.ln(5)

      pdf.set_font("Arial", "B", 11)
      pdf.set_text_color(24, 43, 73)
      pdf.cell(
          200, 8, txt=limpiar_texto("1. INFORMACION TECNICA DEL OBJETIVO"), ln=True
      )

      pdf.set_font("Arial", "", 10)
      pdf.set_text_color(0, 0, 0)
      pdf.set_fill_color(245, 247, 250)

      pdf.cell(
          200,
          7,
          txt=limpiar_texto(f"  - Objetivo / Edificio: {nom}"),
          ln=True,
          fill=True,
      )
      pdf.cell(
          200,
          7,
          txt=limpiar_texto(f"  - Direccion Exacta: {dat['dir']}"),
          ln=True,
          fill=True,
      )
      pdf.cell(
          200,
          7,
          txt=limpiar_texto(f"  - Altura Catastral: {dat['alt']}"),
          ln=True,
          fill=True,
      )
      pdf.cell(
          200,
          7,
          txt=limpiar_texto(f"  - Accesos (Entradas/Salidas): {dat['acc']}"),
          ln=True,
          fill=True,
      )
      pdf.cell(
          200,
          7,
          txt=limpiar_texto(f"  - Coordenadas GPS: {dat['coords']}"),
          ln=True,
          fill=True,
      )
      pdf.ln(5)

      pdf.set_font("Arial", "B", 11)
      pdf.set_text_color(24, 43, 73)
      pdf.cell(
          200,
          8,
          txt=limpiar_texto("2. PUNTOS SEGUROS DE REFERENCIA (CABA)"),
          ln=True,
      )

      pdf.set_font("Arial", "", 10)
      pdf.set_text_color(0, 0, 0)
      pdf.cell(
          200,
          6,
          txt=limpiar_texto(
              "  * Hospital General de Agudos J. A. Fernandez - Cerviño 3356,"
              " Recoleta"
          ),
          ln=True,
      )
      pdf.cell(
          200,
          6,
          txt=limpiar_texto(
              "  * Comisaria Vecinal 1A - Suipacha 1156, Retiro"
          ),
          ln=True,
      )
      pdf.cell(
          200,
          6,
          txt=limpiar_texto(
              "  * Departamento Central de Policia (PFA) - Moreno 1550,"
              " Monserrat"
          ),
          ln=True,
      )
      pdf.cell(
          200,
          6,
          txt=limpiar_texto(
              "  * Edificio Libertador (Min. de Defensa / FFAA) - Azopardo"
              " 250, Monserrat"
          ),
          ln=True,
      )
      pdf.ln(15)

      pdf.set_font("Arial", "B", 10)
      pdf.set_text_color(24, 43, 73)
      pdf.cell(
          200, 6, txt=limpiar_texto("3. VALIDACION Y FIRMA DIGITAL"), ln=True
      )
      pdf.ln(10)

      pdf.set_font("Arial", "", 10)
      pdf.set_text_color(50, 50, 50)
      f_texto = (
          firma_digital
          if firma_digital
          else "Firma Autorizada - Control Operativo SPPRO"
      )
      pdf.cell(
          200, 6, txt="________________________________________________", ln=True
      )
      pdf.cell(
          200, 6, txt=limpiar_texto(f"Certificado Digital: {f_texto}"), ln=True
      )
      pdf.cell(
          200,
          6,
          txt=limpiar_texto(
              "Sello de Verificacion Automatizada SPPRO - Seguridad"
              " Patrimonial"
          ),
          ln=True,
      )

      archivo_pdf = "sppro_verificacion_evento.pdf"
      pdf.output(archivo_pdf)

      registro_auditoria = {
          "fecha": fecha_hora_actual,
          "edificio": nom,
          "firmante": f_texto,
          "clima": clima_actual,
          "fotos_adjuntas": (
              len(st.session_state.get("fotos_cargadas", []))
          ),
      }
      st.session_state["historial_auditoria"].append(registro_auditoria)

      with open(archivo_pdf, "rb") as f:
        st.download_button(
            label="💾 Descargar PDF Profesional Ahora",
            data=f,
            file_name=archivo_pdf,
            mime="application/pdf",
        )
      st.success(
          "¡PDF generado con éxito y registrado en el sistema de auditoría!"
      )
  else:
    st.warning(
        "⚠️ Atención: Primero debe ir a la solapa **1️⃣ Verificación de Edificios**"
        " y verificar un objetivo."
    )


# ==========================================
# SOLAPA 3: AUDITORÍA Y REPORTES PREVIOS
# ==========================================
elif menu == "3️⃣ Auditoria y Reportes":
  st.header("📊 Registro de Auditoría y Reportes Históricos")
  st.markdown(
      "Control de trazabilidad de todas las verificaciones y PDFs emitidos en"
      " la sesión."
  )

  if len(st.session_state["historial_auditoria"]) == 0:
    st.info(
        "Aún no se han generado reportes en esta sesión. Los registros"
        " aparecerán aquí automáticamente."
    )
  else:
    st.success(
        f"Total de reportes emitidos: {len(st.session_state['historial_auditoria'])}"
    )

    for i, item in enumerate(
        reversed(st.session_state["historial_auditoria"])
    ):
      with st.expander(
          f"📄 Reporte #{len(st.session_state['historial_auditoria']) - i} -"
          f" {item['edificio']} ({item['fecha']})"
      ):
        st.markdown(f"**🏢 Objetivo:** {item['edificio']}")
        st.markdown(f"**📅 Fecha y Hora:** {item['fecha']}")
        st.markdown(f"**✍️ Responsable / Firma:** {item['firmante']}")
        st.markdown(f"**🌡️ Clima registrado:** {item['clima']}")
        st.markdown(
            f"**📷 Archivos fotográficos adjuntos:** {item['fotos_adjuntas']}"
        )


# ==========================================
# SOLAPA 4: ADMINISTRADOR DE USUARIOS
# ==========================================
elif menu == "4️⃣ Administrador de Usuarios":
  st.header("👤 Panel de Administracion de Usuarios")
  st.markdown(
      "Agregue o elimine operadores con acceso autorizado al sistema."
  )

  st.subheader("Operadores Habilitados")
  for user in st.session_state["usuarios_db"]:
    col1, col2 = st.columns([3, 1])
    with col1:
      st.text(f"👤 {user}")
    with col2:
      if st.button("🗑️ Borrar", key=f"del_{user}"):
        st.session_state["usuarios_db"].remove(user)
        st.rerun()

  st.divider()

  st.subheader("Registrar Nuevo Operador")
  with st.form("agregar_usuario_form"):
    nuevo_usr = st.text_input("Nombre de Usuario / Legajo")
    btn_agregar = st.form_submit_button("Dar de Alta Usuario")

    if btn_agregar and nuevo_usr:
      if nuevo_usr not in st.session_state["usuarios_db"]:
        st.session_state["usuarios_db"].append(nuevo_usr)
        st.success(f"Usuario '{nuevo_usr}' agregado con éxito.")
        st.rerun()
      else:
        st.error("El usuario ya existe en el sistema.")
