import os
import sqlite3
from datetime import datetime
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SPPRO - Seguridad Patrimonial",
    page_icon="🛡️",
    layout="wide",
)

# --- BASE DE DATOS (SQLite Simple para demo/operación) ---


def init_db():
  conn = sqlite3.connect("sppro_database.db")
  cursor = conn.cursor()

  # Tabla de Edificios
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS edificios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            direccion TEXT,
            altura TEXT,
            accesos TEXT,
            coordenadas TEXT
        )
    """)

  # Tabla de Usuarios
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            activo BOOLEAN
        )
    """)

  # Precargar edificios emblemáticos de CABA si está vacía
  cursor.execute("SELECT COUNT(*) FROM edificios")
  if cursor.fetchone()[0] == 0:
    emblematicos = [
        (
            "Edificio Kavanagh",
            "Florida 1065, Retiro",
            "120 m",
            "Principal y Cochera",
            "-34.5922, -58.3753",
        ),
        (
            "Palacio Barolo",
            "Av. de Mayo 1370, Monserrat",
            "100 m",
            "Acceso Principal y Carga",
            "-34.6095, -58.3860",
        ),
        (
            "Libertador (Edificio Libertador)",
            "Azopardo 250, Monserrat",
            "45 m",
            "Acceso Norte y Sur",
            "-34.6118, -58.3695",
        ),
    ]
    cursor.executemany(
        "INSERT INTO edificios (nombre, direccion, altura, accesos,"
        " coordenadas) VALUES (?, ?, ?, ?, ?)",
        emblematicos,
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

# --- NAVEGACIÓN POR SOLAPAS ---
tab1, tab2, tab3 = st.tabs(
    [
        "1️⃣ Verificación de Edificios",
        "2️⃣ Generación de PDF",
        "3️⃣ Administrador de Usuarios",
    ]
)

# ==========================================
# SOLAPA 1: VERIFICACIÓN DE EDIFICIOS
# ==========================================
with tab1:
  st.subheader("Control y Verificación de Edificios")

  # Conexión para consultas
  conn = sqlite3.connect("sppro_database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT nombre FROM edificios")
  lista_edificios = [row[0] for row in cursor.fetchall()]
  conn.close()

  # Selección del modo de origen de datos
  modo_edificio = st.radio(
      "Seleccione método:",
      [
          "🏢 Seleccionar de Edificios Emblemáticos CABA",
          "✏️ Ingresar / Editar Edificio Nuevo",
      ],
      horizontal=True,
  )

  edificio_seleccionado = None

  if modo_edificio.startswith("🏢"):
    edificio_seleccionado = st.selectbox(
        "Elija el edificio:", lista_edificios
    )
  else:
    with st.form("form_nuevo_edificio"):
      st.info("Ingrese los datos del nuevo edificio:")
      nuevo_nombre = st.text_input("Nombre del Edificio")
      nueva_dir = st.text_input("Dirección")
      nueva_alt = st.text_input("Altura Catastral (ej. 45 m)")
      nuevos_acc = st.text_input("Entradas y Salidas (ej. Principal y Emergencia)")
      nuevas_coord = st.text_input("Coordenadas GPS")
      guardar_btn = st.form_submit_button("Guardar y Seleccionar")

      if guardar_btn and nuevo_nombre:
        try:
          conn = sqlite3.connect("sppro_database.db")
          cursor = conn.cursor()
          cursor.execute(
              "INSERT OR REPLACE INTO edificios (nombre, direccion, altura,"
              " accesos, coordenadas) VALUES (?, ?, ?, ?, ?)",
              (
                  nuevo_nombre,
                  nueva_dir,
                  nueva_alt,
                  nuevos_acc,
                  nuevas_coord,
              ),
          )
          conn.commit()
          conn.close()
          st.success(f"Edificio '{nuevo_nombre}' guardado correctamente.")
          edificio_seleccionado = nuevo_nombre
        except Exception as e:
          st.error(f"Error al guardar: {e}")

  st.divider()

  # Botón principal de verificación
  if st.button("🔍 Verificar Edificio", type="primary"):
    if edificio_seleccionado:
      conn = sqlite3.connect("sppro_database.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT direccion, altura, accesos, coordenadas FROM edificios WHERE"
          " nombre = ?",
          (edificio_seleccionado,),
      )
      datos = cursor.fetchone()
      conn.close()

      if datos:
        st.session_state["edificio_activo"] = edificio_seleccionado
        st.session_state["datos_activo"] = datos

  # Mostrar datos si ya se presionó verificar
  if "edificio_activo" in st.session_state:
    nombre_act = st.session_state["edificio_activo"]
    dir_act, alt_act, acc_act, coord_act = st.session_state["datos_activo"]

    st.markdown(f"### 📍 Ficha Técnica: {nombre_act}")

    col1, col2 = st.columns(2)
    with col1:
      st.markdown(f"**Dirección:** {dir_act}")
      st.markdown(f"**Altura Catastral:** {alt_act}")
    with col2:
      st.markdown(f"**Entradas y Salidas:** {acc_act}")
      st.markdown(f"**Coordenadas:** {coord_act}")

    st.markdown("---")
    st.subheader("📷 Carga de Imágenes / Evidencia")
    fotos_cargadas = st.file_uploader(
        "Subir fotos para futuros eventos (Historial)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if fotos_cargadas:
      st.success(
          f"{len(fotos_cargadas)} imagen(es) listas para adjuntar al registro"
          " de eventos."
      )

    st.markdown("---")
    st.subheader("🛡️ Puntos Seguros Cercanos (CABA)")

    # Puntos seguros precargados simulados (Hospitales, PFA, FFAA)
    puntos_seguros = [
        {
            "tipo": "🏥 Hospital",
            "nombre": "Hospital General de Agudos J. A. Fernández",
            "dir": "Cerviño 3356",
        },
        {
            "tipo": "🚨 Comisaría",
            "nombre": "Comisaría Vecinal 1A",
            "dir": "Suipacha 1156",
        },
        {
            "tipo": "🏛️ Edificio PFA",
            "nombre": "Departamento Central de Policía",
            "dir": "Av. Cnel. Díaz 1850",
        },
        {
            "tipo": "⭐ Edificio FF.AA.",
            "nombre": "Edificio Libertador (Min. de Defensa)",
            "dir": "Azopardo 250",
        },
    ]

    for p in puntos_seguros:
      st.info(f"**{p['tipo']}**: {p['nombre']} — 📌 {p['dir']}")


# ==========================================
# SOLAPA 2: GENERACIÓN DE PDF
# ==========================================
with tab2:
  st.subheader("Generación de Reportes en PDF")
  st.markdown(
      "Desde aquí podrás exportar el reporte integral con todos los datos del"
      " edificio verificado, accesos y puntos seguros asociados."
  )

  if "edificio_activo" in st.session_state:
    st.success(
        "Edificio seleccionado para reporte:"
        f" **{st.session_state['edificio_activo']}**"
    )

    if st.button("📄 Generar y Descargar PDF", type="primary"):
      # Espacio para integrar ReportLab o la lógica de generación PDF que prefieras
      st.info(
          "Generando documento PDF con los datos técnicos y registros"
          " fotográficos... (Función de exportación lista para conectar con"
          " ReportLab)."
      )
  else:
    st.warning(
        "⚠️ Primero debés seleccionar y verificar un edificio en la Solapa 1."
    )


# ==========================================
# SOLAPA 3: ADMINISTRADOR DE USUARIOS
# ==========================================
with tab3:
  st.subheader("Panel de Administración de Usuarios")
  st.markdown(
      "Habilitá o deshabilitá el acceso al personal para mantener la seguridad"
      " operativa de la plataforma."
  )

  conn = sqlite3.connect("sppro_database.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, username, activo FROM usuarios")
  usuarios = cursor.fetchall()

  st.markdown("### Lista de Operadores")
  for u_id, uname, u_activo in usuarios:
    col_u1, col_u2, col_u3 = st.columns([3, 2, 2])
    with col_u1:
      st.text(f"👤 {uname}")
    with col_u2:
      estado_txt = "🟢 Habilitado" if u_activo else "🔴 Deshabilitado"
      st.text(estado_txt)
    with col_u3:
      nuevo_estado = not u_activo
      label_boton = "Deshabilitar" if u_activo else "Habilitar"
      if st.button(label_boton, key=f"btn_user_{u_id}"):
        cursor.execute(
            "UPDATE usuarios SET activo = ? WHERE id = ?", (nuevo_estado, u_id)
        )
        conn.commit()
        st.rerun()

  st.divider()
  st.markdown("### Agregar Nuevo Usuario")
  with st.form("nuevo_usuario_form"):
    nuevo_user = st.text_input("Nombre de usuario / Legajo")
    crear_user_btn = st.form_submit_button("Crear Usuario")
    if crear_user_btn and nuevo_user:
      try:
        cursor.execute(
            "INSERT INTO usuarios (username, activo) VALUES (?, ?)",
            (nuevo_user, True),
        )
        conn.commit()
        st.success(f"Usuario {nuevo_user} agregado con éxito.")
        st.rerun()
      except Exception as e:
        st.error(f"Error: El usuario ya existe o hubo un fallo ({e}).")

  conn.close()
