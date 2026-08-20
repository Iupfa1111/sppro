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


# --- BASE DE DATOS COMPLETA DE PUNTOS SEGUROS (HOSPITALES + COMISARÍAS + PFA) ---
puntos_seguros = {
    # --- HOSPITALES GENERALES DE AGUDOS ---
    "Hospital Alvarez (Flores)": (-34.6190, -58.4610),
    "Hospital Argerich (La Boca)": (-34.6366, -58.3639),
    "Hospital Durand (Caballito)": (-34.6111, -58.4347),
    "Hospital Fernández (Palermo)": (-34.5833, -58.4069),
    "Hospital Cecilia Grierson (Lugano)": (-34.6852, -58.4612),
    "Hospital Penna (Parque Patricios)": (-34.6432, -58.3912),
    "Hospital Piñero (Flores)": (-34.6432, -58.4412),
    "Hospital Pirovano (Coghlan)": (-34.5583, -58.4839),
    "Hospital Ramos Mejía (Balvanera)": (-34.6152, -58.4079),
    "Hospital Rivadavia (Recoleta)": (-34.5852, -58.3976),
    "Hospital Santojanni (Liniers)": (-34.6531, -58.5134),
    "Hospital Tornú (Villa Ortúzar)": (-34.5856, -58.4812),
    "Hospital Vélez Sarsfield (Monte Castro)": (-34.6291, -58.5089),
    "Hospital Zubizarreta (Villa Devoto)": (-34.5954, -58.5176),
    "Hospital de Clínicas (Recoleta)": (-34.5983, -58.3986),
    # --- COMISARÍAS VECINALES Y COMUNALES DE CABA ---
    "Comisaría Comunal 1 / Vecinal 1-A (Retiro)": (-34.5842, -58.3695),
    "Comisaría Vecinal 1-B (Monserrat / San Telmo)": (-34.6177, -58.3803),
    "Comisaría Vecinal 1-C (Constitución)": (-34.6251, -58.3814),
    "Comisaría Vecinal 1-D (San Nicolás)": (-34.6033, -58.3872),
    "Comisaría Vecinal 1-E (Puerto Madero)": (-34.6201, -58.3614),
    "Comisaría Comunal 2 / Vecinal 2-A (Recoleta)": (-34.5911, -58.3923),
    "Comisaría Vecinal 2-B (Recoleta Norte)": (-34.5950, -58.3960),
    "Comisaría Comunal 3 (Balvanera / San Cristóbal)": (-34.6149, -58.3936),
    "Comisaría Vecinal 3-A (Balvanera)": (-34.6021, -58.3980),
    "Comisaría Vecinal 3-B (San Cristóbal)": (-34.6210, -58.4050),
    "Comisaría Comunal 4 (Parque Patricios)": (-34.6419, -58.4028),
    "Comisaría Vecinal 4-A (Barracas)": (-34.6470, -58.3750),
    "Comisaría Vecinal 4-B (La Boca)": (-34.6342, -58.3639),
    "Comisaría Vecinal 4-C (Nueva Pompeya)": (-34.6510, -58.4110),
    "Comisaría Vecinal 4-D (Barracas Sur)": (-34.6550, -58.3850),
    "Comisaría Comunal 5 / Vecinal 5-A (Almagro)": (-34.6044, -58.4156),
    "Comisaría Vecinal 5-B (Boedo)": (-34.6220, -58.4210),
    "Comisaría Comunal 6 / Vecinal 6-B (Caballito)": (-34.6203, -58.4532),
    "Comisaría Vecinal 6-A (Caballito Norte)": (-34.6100, -58.4400),
    "Comisaría Comunal 7 / Vecinal 7-A (Flores)": (-34.6310, -58.4583),
    "Comisaría Vecinal 7-B (Parque Chacabuco)": (-34.6380, -58.4420),
    "Comisaría Vecinal 7-C (Flores Norte)": (-34.6150, -58.4700),
    "Comisaría Comunal 8 (Villa Soldati)": (-34.6712, -58.4551),
    "Comisaría Vecinal 8-A (Villa Riachuelo)": (-34.6850, -58.4500),
    "Comisaría Vecinal 8-B (Villa Lugano)": (-34.6800, -58.4650),
    "Comisaría Vecinal 8-C (Linderos Soldati)": (-34.6650, -58.4450),
    "Comisaría Comunal 9 / Vecinal 9-A (Liniers)": (-34.6451, -58.5252),
    "Comisaría Vecinal 9-B (Mataderos)": (-34.6580, -58.5020),
    "Comisaría Vecinal 9-C (Parque Avellaneda)": (-34.6420, -58.4750),
    "Comisaría Comunal 10 (Villa Luro)": (-34.6391, -58.4940),
    "Comisaría Vecinal 10-A (Villa Real / Monte Castro)": (-34.6210, -58.5150),
    "Comisaría Vecinal 10-B (Velez Sarsfield)": (-34.6300, -58.4850),
    "Comisaría Vecinal 10-C (Floresta)": (-34.6320, -58.4800),
    "Comisaría Comunal 11 (Villa Devoto)": (-34.6110, -58.4729),
    "Comisaría Vecinal 11-A (Villa General Mitre)": (-34.6050, -58.4650),
    "Comisaría Vecinal 11-B (Villa Santa Rita / Devoto)": (-34.6000, -58.4900),
    "Comisaría Comunal 12 (Saavedra)": (-34.5509, -58.4910),
    "Comisaría Vecinal 12-A (Coghlan)": (-34.5650, -58.4750),
    "Comisaría Vecinal 12-B (Villa Urquiza)": (-34.5750, -58.4850),
    "Comisaría Vecinal 12-C (Saavedra Este)": (-34.5600, -58.4950),
    "Comisaría Comunal 13 (Núñez / Belgrano)": (-34.5552, -58.4591),
    "Comisaría Vecinal 13-A (Belgrano R)": (-34.5700, -58.4600),
    "Comisaría Vecinal 13-B (Colegiales)": (-34.5780, -58.4500),
    "Comisaría Vecinal 13-C (Nuñez)": (-34.5450, -58.4650),
    "Comisaría Comunal 14 (Palermo)": (-34.5812, -58.4136),
    "Comisaría Vecinal 14-A (Palermo Botánico)": (-34.5850, -58.4200),
    "Comisaría Vecinal 14-B (Palermo Soho / Alto Palermo)": (-34.5900, -58.4100),
    "Comisaría Vecinal 14-C (Palermo Hollywood)": (-34.5800, -58.4350),
    "Comisaría Comunal 15 (Chacarita / Villa Crespo)": (-34.5905, -58.4510),
    "Comisaría Vecinal 15-A (La Paternal)": (-34.5980, -58.4600),
    "Comisaría Vecinal 15-B (Agronomía)": (-34.5850, -58.4900),
    "Comisaría Vecinal 15-C (Parque Chas)": (-34.5780, -58.4800),
    # --- DESTINOS ESPECIALES PFA ---
    "Superintendencia de Policía Científica (PFA)": (-34.6135, -58.3912),
    "Dirección General de Cuerpos - Policía Montada (PFA)": (-34.6195, -58.3792),
    "Departamento de Cuerpo Motorizado (PFA)": (-34.6241, -58.3855),
    "Departamento Central de Policía (PFA - Monserrat)": (-34.6146, -58.3848),
}


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

  # Listado ordenado alfabéticamente
  lista_nombres = sorted(list(st.session_state["edificios_db"].keys()))
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

    # Cálculo dinámico del punto seguro más cercano
    lat_edif, lon_edif = map(float, dat["coords"].split(","))
    distancias = {
        nombre: ((c[0] - lat_edif) ** 2 + (c[1] - lon_edif) ** 2) ** 0.5
        for nombre, c in puntos_seguros.items()
    }
    mas_cercano = min(distancias, key=distancias.get)

    st.markdown("---")
    st.subheader(
        "🛡️ Punto Seguro Más Cercano (Hospital / Comisaría / Destino PFA)"
    )
    st.success(f"📍 Destino recomendado por cercanía: **{mas_cercano}**")

    st.markdown("---")
    st.subheader("🔗 Enlaces de Interés y Pruebas")
    st.markdown(
        "👥 [Ir a sección de prueba de personal (Enlace externo)]"
        "(https://github.com/lupfa111/sppro)",
        unsafe_allow_html=True,
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
      # Cálculo para el PDF
      lat_edif, lon_edif = map(float, dat["coords"].split(","))
      distancias = {
          nombre: ((c[0] - lat_edif) ** 2 + (c[1] - lon_edif) ** 2) ** 0.5
          for nombre, c in puntos_seguros.items()
      }
      mas_cercano = min(distancias, key=distancias.get)

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
      pdf.set_text_color(24, 4 
