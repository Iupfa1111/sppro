import os
import sqlite3
import datetime
import pandas as pd
import streamlit as st
from fpdf import FPDF
from PIL import Image
import clima

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SPPRO by Angel Ibañez", layout="wide")

# --- ESTILOS VISUALES (Azul Institucional) ---
st.markdown("""
    <style>
        .stButton>button { background-color: #003366; color: white; border-radius: 4px; }
        .stButton>button:hover { background-color: #002244; color: white; }
        h1, h2, h3 { color: #003366; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# BASE DE DATOS Y AUTOCORRECCIÓN
# ==========================================
def init_db():
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    
    # Tabla usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            activo INTEGER NOT NULL,
            rol TEXT NOT NULL
        )
    """)
    
    # Tabla edificios (Objetivos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edificios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT,
            direccion TEXT NOT NULL,
            altura TEXT,
            latitud REAL,
            longitud REAL,
            pisos INTEGER,
            subsuelos INTEGER,
            horario TEXT,
            observaciones TEXT
        )
    """)

    # Tabla fotografías asociadas a edificios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fotografias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edificio_id INTEGER,
            archivo TEXT,
            descripcion TEXT,
            usuario TEXT,
            fecha TEXT,
            FOREIGN KEY(edificio_id) REFERENCES edificios(id)
        )
    """)

    # Tabla cámaras observadas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS camaras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edificio_id INTEGER,
            ubicacion TEXT,
            observacion TEXT,
            FOREIGN KEY(edificio_id) REFERENCES edificios(id)
        )
    """)

    # Tabla puntos de apoyo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS puntos_apoyo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            tipo TEXT,
            direccion TEXT,
            observaciones TEXT
        )
    """)

    # Tabla checklist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edificio_id INTEGER,
            item TEXT,
            verificado INTEGER,
            FOREIGN KEY(edificio_id) REFERENCES edificios(id)
        )
    """)

    # Crear usuario administrador por defecto si no existe
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("admin", "admin123", 1, "Administrador"))
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("operador1", "user123", 1, "Operador"))
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# FUNCIONES DE UTILIDAD (PDF y Texto)
# ==========================================
def limpiar_texto(texto):
    if not texto:
        return ""
    return str(texto).replace("•", "-").encode('latin-1', 'ignore').decode('latin-1')

class PDFReporte(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.set_text_color(0, 51, 102) # Azul institucional
        self.cell(0, 10, limpiar_texto("SPPRO"), ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 6, limpiar_texto("Informe de Verificación"), ln=True, align="C")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", "", 9)
        self.cell(0, 5, limpiar_texto("____________"), 0, 1, "C")
        self.cell(0, 5, limpiar_texto("Firma del operador"), 0, 1, "C")
        self.ln(2)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, limpiar_texto("SPPRO\nby Angel Ibañez"), 0, 0, "R")

# ==========================================
# ESTADOS DE SESIÓN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None

# ==========================================
# LOGIN
# ==========================================
if not st.session_state["logged_in"]:
    st.title("SPPRO")
    st.caption("by Angel Ibañez - Seguridad Patrimonial")
    st.divider()
    
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.subheader("Acceso al Sistema")
        usuario_ingresado = st.text_input("Usuario")
        clave_ingresada = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", use_container_width=True):
            conn = sqlite3.connect("sppro.db")
            cursor = conn.cursor()
            cursor.execute("SELECT password, activo, rol FROM usuarios WHERE username = ?", (usuario_ingresado,))
            res = cursor.fetchone()
            conn.close()
            
            if res and res[0] == clave_ingresada:
                if res[1] == 1:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = usuario_ingresado
                    st.session_state["user_role"] = res[2]
                    st.rerun()
                else:
                    st.error("⚠️ Usuario desactivado por el administrador.")
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
    st.stop()

# ==========================================
# MENÚ PRINCIPAL Y NAVEGACIÓN
# ==========================================
st.sidebar.title(f"SPPRO | {st.session_state['username']}")
st.sidebar.caption(f"Rol: {st.session_state['user_role']}")

menu_items = ["🏢 Verificación de Objetivos", "🏥 Puntos de Apoyo", "🌦️ Clima"]
if st.session_state["user_role"] == "Administrador":
    menu_items.append("👥 Gestión de Usuarios")

seccion = st.sidebar.radio("Navegación:", menu_items)

st.sidebar.divider()
if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("SPPRO by Angel Ibañez")

# ==========================================
# SECCIÓN 1: VERIFICACIÓN DE OBJETIVOS
# ==========================================
if seccion == "🏢 Verificación de Objetivos":
    st.header("🏢 Verificación de Objetivos")
    
    tab_list, tab_new = st.tabs(["📋 Consultar / Historial", "➕ Nuevo Objetivo"])
    
    with tab_new:
        st.subheader("Registrar Nuevo Objetivo")
        with st.form("form_nuevo_objetivo"):
            nombre = st.text_input("Nombre del objetivo *")
            tipo = st.selectbox("Tipo de objetivo", ["Edificio", "Hotel", "Empresa", "Comercio", "Organismo público", "Institución", "Otro"])
            direccion = st.text_input("Dirección *")
            altura = st.text_input("Altura catastral")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                latitud = st.number_input("Latitud (Manual)", format="%.6f", value=0.0)
            with col_c2:
                longitud = st.number_input("Longitud (Manual)", format="%.6f", value=0.0)
                
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                pisos = st.number_input("Cantidad de pisos", min_value=0, value=1)
            with col_p2:
                subsuelos = st.number_input("Cantidad de subsuelos", min_value=0, value=0)
                
            horario = st.text_input("Horario de funcionamiento")
            observaciones = st.text_area("Observaciones generales")
            
            submitted = st.form_submit_button("Guardar Objetivo")
            if submitted:
                if nombre and direccion:
                    conn = sqlite3.connect("sppro.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO edificios (nombre, tipo, direccion, altura, latitud, longitud, pisos, subsuelos, horario, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nombre, tipo, direccion, altura, latitud, longitud, pisos, subsuelos, horario, observaciones))
                    conn.commit()
                    conn.close()
                    st.success("✅ Objetivo registrado exitosamente.")
                else:
                    st.error("⚠️ El nombre y la dirección son obligatorios.")

    with tab_list:
        st.subheader("Consultar Objetivos Registrados")
        conn = sqlite3.connect("sppro.db")
        df_edificios = pd.read_sql("SELECT * FROM edificios", conn)
        conn.close()
        
        if df_edificios.empty:
            st.info("No hay objetivos registrados en el sistema.")
        else:
            for idx, row in df_edificios.iterrows():
                edf_id = row["id"]
                with st.expander(f"🏢 {row['nombre']} ({row['tipo'] or 'General'}) - {row['direccion']}"):
                    st.write(f"*Dirección:* {row['direccion']} | *Altura:* {row['altura']}")
                    st.write(f"*Coordenadas:* Lat: {row['latitud']}, Lon: {row['longitud']}")
                    st.write(f"*Pisos:* {row['pisos']} | *Subsuelos:* {row['subsuelos']} | *Horario:* {row['horario']}")
                    st.write(f"*Observaciones:* {row['observaciones']}")
                    
                    # Cargar datos asociados
                    conn = sqlite3.connect("sppro.db")
                    c = conn.cursor()
                    c.execute("SELECT archivo, descripcion FROM fotografias WHERE edificio_id = ?", (edf_id,))
                    fotos = c.fetchall()
                    c.execute("SELECT ubicacion, observacion FROM camaras WHERE edificio_id = ?", (edf_id,))
                    camaras = c.fetchall()
                    conn.close()
                    
                    st.markdown(f"---")
                    st.markdown(f"*Fotografías registradas:* {len(fotos)} | *Cámaras registradas:* {len(camaras)}")
                    
                    # Subir nueva fotografía
                    with st.form(f"form_foto_{edf_id}"):
                        st.markdown("### ➕ Agregar Fotografía")
                        desc_foto = st.text_input("Descripción de la fotografía (ej. Fachada, Acceso principal)", key=f"desc_{edf_id}")
                        archivo_subido = st.file_uploader("Seleccionar imagen", type=["jpg", "jpeg", "png"], key=f"file_{edf_id}")
                        btn_subir_foto = st.form_submit_button("Guardar Fotografía")
                        
                        if btn_subir_foto and archivo_subido:
                            dir_fotos = f"fotos/edificio_{edf_id}"
                            os.makedirs(dir_fotos, exist_ok=True)
                            ruta_archivo = os.path.join(dir_fotos, archivo_subido.name)
                            with open(ruta_archivo, "wb") as f:
                                f.write(archivo_subido.getbuffer())
                                
                            conn = sqlite3.connect("sppro.db")
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO fotografias (edificio_id, archivo, descripcion, usuario, fecha) VALUES (?, ?, ?, ?, ?)",
                                           (edf_id, ruta_archivo, desc_foto or "Sin descripción", st.session_state["username"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
                            conn.commit()
                            conn.close()
                            st.success("✅ Fotografía guardada persistentemente.")
                            st.rerun()

                    # Registro manual de cámaras
                    with st.form(f"form_cam_{edf_id}"):
                        st.markdown("### 🎥 Registrar Cámara")
                        ubicacion_cam = st.text_input("Ubicación de la cámara (ej. Acceso principal)", key=f"ucam_{edf_id}")
                        obs_cam = st.text_input("Observación", key=f"ocam_{edf_id}")
                        btn_cam = st.form_submit_button("Guardar Cámara")
                        
                        if btn_cam and ubicacion_cam:
                            conn = sqlite3.connect("sppro.db")
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO camaras (edificio_id, ubicacion, observacion) VALUES (?, ?, ?)",
                                           (edf_id, ubicacion_cam, obs_cam))
                            conn.commit()
                            conn.close()
                            st.success("✅ Cámara registrada.")
                            st.rerun()

                    # Generación de Informe PDF Profesional
                    st.markdown("### 📄 Generar Informe PDF")
                    
                    # Selección de fotografías para el PDF
                    fotos_seleccionadas = []
                    if fotos:
                        st.markdown("Seleccione fotografías para incluir en el informe:")
                        for foto in fotos:
                            ruta_f, desc_f = foto[0], foto[1]
                            if st.checkbox(f"{desc_f} ({os.path.basename(ruta_f)})", value=True, key=f"chk_f_{edf_id}_{ruta_f}"):
                                fotos_seleccionadas.append(foto)
                                
                    if st.button("Descargar PDF de este Objetivo", key=f"pdf_{edf_id}"):
                        pdf = PDFReporte()
                        pdf.add_page()
                        pdf.set_font("Arial", "B", 12)
                        pdf.set_text_color(0, 51, 102)
                        
                        # 1. IDENTIFICACIÓN DEL OBJETIVO
                        pdf.cell(0, 8, limpiar_texto("IDENTIFICACIÓN DEL OBJETIVO"), ln=True)
                        pdf.set_font("Arial", "", 10)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(0, 6, limpiar_texto(f"Nombre: {row['nombre']}"), ln=True)
                        pdf.cell(0, 6, limpiar_texto(f"Tipo: {row['tipo']}"), ln=True)
                        pdf.cell(0, 6, limpiar_texto(f"Dirección: {row['direccion']} (Altura: {row['altura']})"), ln=True)
                        pdf.cell(0, 6, limpiar_texto(f"Coordenadas: Lat: {row['latitud']}, Lon: {row['longitud']}"), ln=True)
                        pdf.cell(0, 6, limpiar_texto(f"Pisos: {row['pisos']} | Subsuelos: {row['subsuelos']}"), ln=True)
                        pdf.cell(0, 6, limpiar_texto(f"Horario de funcionamiento: {row['horario']}"), ln=True)
                        pdf.ln(4)
                        
                        # 2. CONDICIONES METEOROLÓGICAS
                        pdf.set_font("Arial", "B", 12)
                        pdf.set_text_color(0, 51, 102)
                        pdf.cell(0, 8, limpiar_texto("CONDICIONES METEOROLÓGICAS"), ln=True)
                        pdf.set_font("Arial", "", 10)
                        pdf.set_text_color(0, 0, 0)
                        clima_actual = clima.obtener_clima()
                        if clima_actual:
                            pdf.cell(0, 6, limpiar_texto(f"Temperatura: {clima_actual['temperatura']} | Estado: {clima_actual['estado']}"), ln=True)
                            pdf.cell(0, 6, limpiar_texto(f"Viento: {clima_actual['viento']} | Humedad: {clima_actual['humedad']} | Presión: {clima_actual['presion']}"), ln=True)
                        else:
                            pdf.cell(0, 6, limpiar_texto("⚠️ Información meteorológica no disponible."), ln=True)
                        pdf.ln(4)

                        # 3. CÁMARAS OBSERVADAS
                        if camaras:
                            pdf.set_font("Arial", "B", 12)
                            pdf.set_text_color(0, 51, 102)
                            pdf.cell(0, 8, limpiar_texto("CÁMARAS OBSERVADAS"), ln=True)
                            pdf.set_font("Arial", "", 10)
                            pdf.set_text_color(0, 0, 0)
                            for idx_c, cam in enumerate(camaras, 1):
                                pdf.cell(0, 6, limpiar_texto(f"Cámara {idx_c:02d} - Ubicación: {cam[0]} | Observación: {cam[1]}"), ln=True)
                            pdf.ln(4)

                        # 4. PUNTOS DE APOYO
                        conn_p = sqlite3.connect("sppro.db")
                        puntos_db = pd.read_sql("SELECT * FROM puntos_apoyo", conn_p).values.tolist()
                        conn_p.close()
                        if puntos_db:
                            pdf.set_font("Arial", "B", 12)
                            pdf.set_text_color(0, 51, 102)
                            pdf.cell(0, 8, limpiar_texto("PUNTOS DE APOYO"), ln=True)
                            pdf.set_font("Arial", "", 10)
                            pdf.set_text_color(0, 0, 0)
                            for pt in puntos_db:
                                pdf.cell(0, 6, limpiar_texto(f"[{pt[2]}] {pt[1]} - {pt[3]} ({pt[4]})"), ln=True)
                            pdf.ln(4)

                        # 5. REGISTRO FOTOGRÁFICO SELECCIONADO
                        if fotos_seleccionadas:
                            pdf.set_font("Arial", "B", 12)
                            pdf.set_text_color(0, 51, 102)
                            pdf.cell(0, 8, limpiar_texto("REGISTRO FOTOGRÁFICO"), ln=True)
                            pdf.set_font("Arial", "", 10)
                            pdf.set_text_color(0, 0, 0)
                            for foto in fotos_seleccionadas:
                                ruta_f, desc_f = foto[0], foto[1]
                                if os.path.exists(ruta_f):
                                    pdf.cell(0, 6, limpiar_texto(f"Foto: {desc_f}"), ln=True)
                                    try:
                                        pdf.image(ruta_f, w=80)
                                        pdf.ln(4)
                                    except:
                                        pass
                            pdf.ln(4)

                        # 6. OBSERVACIONES GENERALES
                        if row["observaciones"]:
                            pdf.set_font("Arial", "B", 12)
                            pdf.set_text_color(0, 51, 102)
                            pdf.cell(0, 8, limpiar_texto("OBSERVACIONES"), ln=True)
                            pdf.set_font("Arial", "", 10)
                            pdf.set_text_color(0, 0, 0)
                            pdf.multi_cell(0, 6, limpiar_texto(row["observaciones"]))

                        pdf_bytes = pdf.output(dest="S").encode("latin-1")
                        st.download_button(
                            label=f"📥 Descargar PDF Generado - {row['nombre']}",
                            data=pdf_bytes,
                            file_name=f"Informe_SPPRO_{row['nombre'].replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key=f"dl_final_{edf_id}"
                        )

# ==========================================
# SECCIÓN 2: PUNTOS DE APOYO
# ==========================================
elif seccion == "🏥 Puntos de Apoyo":
    st.header("🏥 Puntos de Apoyo")
    
    tab_p1, tab_p2 = st.tabs(["Listado", "Agregar Punto de Apoyo"])
    
    with tab_p2:
        with st.form("form_punto_apoyo"):
            nombre_pa = st.text_input("Nombre")
            tipo_pa = st.selectbox("Categoría", ["Hospitales", "Comisarías", "Bomberos", "Defensa Civil", "Otros"])
            dir_pa = st.text_input("Dirección")
            obs_pa = st.text_area("Observaciones")
            
            if st.form_submit_button("Guardar Punto de Apoyo"):
                if nombre_pa:
                    conn = sqlite3.connect("sppro.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO puntos_apoyo (nombre, tipo, direccion, observaciones) VALUES (?, ?, ?, ?)",
                              (nombre_pa, tipo_pa, dir_pa, obs_pa))
                    conn.commit()
                    conn.close()
                    st.success("✅ Punto de apoyo registrado correctamente.")
                else:
                    st.error("⚠️ El nombre es obligatorio.")
                    
    with tab_p1:
        conn = sqlite3.connect("sppro.db")
        df_pa = pd.read_sql("SELECT * FROM puntos_apoyo", conn)
        conn.close()
        
        if df_pa.empty:
            st.info("No hay puntos de apoyo registrados.")
        else:
            st.dataframe(df_pa, use_container_width=True)

# ==========================================
# SECCIÓN 3: CLIMA
# ==========================================
elif seccion == "🌦️ Clima":
    st.header("🌦️ Condiciones Meteorológicas")
    datos_clima = clima.obtener_clima()
    
    if datos_clima:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temperatura", datos_clima["temperatura"])
            st.metric("Estado del cielo", datos_clima["estado"])
        with col2:
            st.metric("Viento", datos_clima["viento"])
            st.metric("Humedad", datos_clima["humedad"])
        with col3:
            st.metric("Presión", datos_clima["presion"])
        st.caption(f"Última actualización: {datos_clima['actualizacion']}")
    else:
        st.warning("⚠️ Información meteorológica no disponible.")

# ==========================================
# SECCIÓN 4: GESTIÓN DE USUARIOS
# ==========================================
elif seccion == "👥 Gestión de Usuarios":
    if st.session_state["user_role"] != "Administrador":
        st.error("⛔ Acceso denegado.")
        st.stop()
        
    st.header("👥 Gestión de Usuarios")
    
    with st.form("nuevo_usuario_admin"):
        st.subheader("Crear Usuario")
        nuevo_user = st.text_input("Username")
        nuevo_pass = st.text_input("Password", type="password")
        nuevo_rol = st.selectbox("Rol", ["Administrador", "Operador"])
        
        if st.form_submit_button("Crear"):
            if nuevo_user and nuevo_pass:
                try:
                    conn = sqlite3.connect("sppro.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO usuarios VALUES (?, ?, 1, ?)", (nuevo_user, nuevo_pass, nuevo_rol))
                    conn.commit()
                    conn.close()
                    st.success("✅ Usuario creado exitosamente.")
                    st.rerun()
                except:
                    st.error("❌ El usuario ya existe.")
            else:
                st.warning("⚠️ Complete los campos.")

    st.divider()
    st.subheader("Usuarios Registrados")
    conn = sqlite3.connect("sppro.db")
    df_users = pd.read_sql("SELECT username, activo, rol FROM usuarios", conn)
    conn.close()
    
    for _, row in df_users.iterrows():
        cols = st.columns([2, 1, 1, 1])
        cols[0].write(row["username"])
        cols[1].write(row["rol"])
        cols[2].write("🟢 Activo" if row["activo"] == 1 else "🔴 Inactivo")
        if row["username"] != "admin":
            if row["activo"] == 1:
                if cols[3].button("Dar de baja", key=f"baja_{row['username']}"):
                    conn = sqlite3.connect("sppro.db")
                    conn.cursor().execute("UPDATE usuarios SET activo = 0 WHERE username = ?", (row["username"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            else:
                if cols[3].button("Dar de alta", key=f"alta_{row['username']}"):
                    conn = sqlite3.connect("sppro.db")
                    conn.cursor().execute("UPDATE usuarios -> SET activo = 1 WHERE username = ?", (row["username"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
