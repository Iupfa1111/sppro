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

# ==========================================
# BASE DE DATOS Y AUTOCORRECCIÓN
# ==========================================
def init_db():
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            activo INTEGER NOT NULL,
            rol TEXT NOT NULL
        )
    """)
    
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS camaras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edificio_id INTEGER,
            ubicacion TEXT,
            observacion TEXT,
            FOREIGN KEY(edificio_id) REFERENCES edificios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS puntos_apoyo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            tipo TEXT,
            direccion TEXT,
            observaciones TEXT
        )
    """)

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
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, limpiar_texto("SPPRO"), ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 6, limpiar_texto("Informe de Verificacion de Edificio"), ln=True, align="C")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", "", 9)
        self.cell(0, 5, limpiar_texto("____________"), 0, 1, "C")
        self.cell(0, 5, limpiar_texto("Firma del operador"), 0, 1, "C")
        self.ln(2)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, limpiar_texto("SPPRO by Angel Ibanez"), 0, 0, "R")

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
    st.caption("by Angel Ibanez - Seguridad Patrimonial")
    st.divider()
    
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.subheader("Acceso al Sistema")
        usuario_ingresado = st.text_input("Usuario")
        clave_ingresada = st.text_input("Contrasena", type="password")
        
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
                    st.error("Usuario desactivado por el administrador.")
            else:
                st.error("Usuario o contrasena incorrectos.")
    st.stop()

# ==========================================
# MENÚ PRINCIPAL Y NAVEGACIÓN
# ==========================================
st.sidebar.title(f"SPPRO | {st.session_state['username']}")
st.sidebar.caption(f"Rol: {st.session_state['user_role']}")

menu_items = ["Verificación de Edificios", "Puntos de Apoyo", "Clima"]
if st.session_state["user_role"] == "Administrador":
    menu_items.append("Gestion de Usuarios")

seccion = st.sidebar.radio("Navegacion:", menu_items)

st.sidebar.divider()
if st.sidebar.button("Cerrar Sesion", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("SPPRO by Angel Ibanez")

# ==========================================
# SECCIÓN 1: VERIFICACIÓN DE EDIFICIOS
# ==========================================
if seccion == "Verificación de Edificios":
    st.header("Verificación de Edificios")
    
    tab_verif, tab_hist = st.tabs(["Verificar Objetivo", "Historial de Objetivos"])
    
    with tab_verif:
        st.subheader("Selección de Objetivo")
        
        # Diccionario de 30 edificios de CABA
        edificios_caba = {
            "Seleccione un edificio emblemático...": {"dir": "", "tipo": "Edificio", "altura": ""},
            "Casa Rosada": {"dir": "Balcarce 50", "tipo": "Organismo público", "altura": "50"},
            "Edificio Kavanagh": {"dir": "Florida 1065", "tipo": "Edificio", "altura": "1065"},
            "Palacio Estrugamou": {"dir": "Esmeralda y Juncal", "tipo": "Edificio", "altura": "S/N"},
            "Galería Güemes": {"dir": "Florida 165", "tipo": "Comercio", "altura": "165"},
            "Centro Cultural Kirchner (CCK)": {"dir": "Sarmiento 151", "tipo": "Organismo público", "altura": "151"},
            "Catedral Metropolitana": {"dir": "San Martín 27", "tipo": "Institución", "altura": "27"},
            "Cabildo de Buenos Aires": {"dir": "Bolívar 65", "tipo": "Institución", "altura": "65"},
            "Torre Monumental (Torre de los Ingleses)": {"dir": "Av. Dr. José María Ramos Mejía 1315", "tipo": "Edificio", "altura": "1315"},
            "Edificio Comega": {"dir": "Av. Corrientes 222", "tipo": "Edificio", "altura": "222"},
            "Edificio Safico": {"dir": "Av. Corrientes 456", "tipo": "Edificio", "altura": "456"},
            "Banco de Boston": {"dir": "Diagonal Norte y Florida", "tipo": "Edificio", "altura": "S/N"},
            "Centro Naval": {"dir": "Florida y Córdoba", "tipo": "Institución", "altura": "S/N"},
            "Palacio Barolo": {"dir": "Av. de Mayo 1370", "tipo": "Edificio", "altura": "1370"},
            "Congreso de la Nación Argentina": {"dir": "Av. Entre Ríos 179", "tipo": "Organismo público", "altura": "179"},
            "Café Tortoni": {"dir": "Av. de Mayo 825", "tipo": "Comercio", "altura": "825"},
            "Manzana de las Luces": {"dir": "Venezuela 469", "tipo": "Institución", "altura": "469"},
            "Librería de Ávila": {"dir": "Alsina 500", "tipo": "Comercio", "altura": "500"},
            "Teatro Colón": {"dir": "Cerrito 628", "tipo": "Institución", "altura": "628"},
            "Tribunales Federales": {"dir": "Talcahuano 550", "tipo": "Organismo público", "altura": "550"},
            "Palacio de Aguas Corrientes": {"dir": "Av. Córdoba 1950", "tipo": "Edificio", "altura": "1950"},
            "El Ateneo Grand Splendid": {"dir": "Av. Santa Fe 1860", "tipo": "Comercio", "altura": "1860"},
            "Palacio Duhau": {"dir": "Av. Alvear 1661", "tipo": "Hotel", "altura": "1661"},
            "Cementerio de La Recoleta": {"dir": "Junín 1760", "tipo": "Institución", "altura": "1760"},
            "Palacio Pereda (Embajada de Brasil)": {"dir": "Arroyo 1130", "tipo": "Institución", "altura": "1130"},
            "Usina del Arte": {"dir": "Caffarena 1", "tipo": "Institución", "altura": "1"},
            "Hipódromo de Palermo": {"dir": "Av. del Libertador 4101", "tipo": "Comercio", "altura": "4101"},
            "Facultad de Derecho (UBA)": {"dir": "Av. Figueroa Alcorta 2263", "tipo": "Institución", "altura": "2263"},
            "Jardín Botánico Carlos Thays": {"dir": "Av. Santa Fe 3951", "tipo": "Institución", "altura": "3951"},
            "Museo Nacional de Bellas Artes": {"dir": "Av. Del Libertador 1473", "tipo": "Institución", "altura": "1473"},
            "Estadio Monumental (River Plate)": {"dir": "Av. Figueroa Alcorta 7597", "tipo": "Institución", "altura": "7597"}
        }

        # 1. Selección rápida de CABA
        edificio_seleccionado = st.selectbox("1. Selección rápida de Edificios Emblemáticos CABA:", list(edificios_caba.keys()))
        
        datos_sugeridos = edificios_caba[edificio_seleccionado] if edificio_seleccionado != "Seleccione un edificio emblemático..." else {"dir": "", "tipo": "Edificio", "altura": ""}

        st.divider()

        # 2. Parte personalizada
        st.subheader("2. Datos Personalizados / Edición del Objetivo")
        with st.form("form_verificacion_objetivo"):
            nombre_input = st.text_input("Nombre del objetivo *", value="" if edificio_seleccionado == "Seleccione un edificio emblemático..." else edificio_seleccionado)
            tipo_input = st.selectbox("Tipo de objetivo", ["Edificio", "Hotel", "Empresa", "Comercio", "Organismo público", "Institución", "Otro"])
            direccion_input = st.text_input("Dirección *", value=datos_sugeridos["dir"])
            altura_input = st.text_input("Altura catastral", value=datos_sugeridos["altura"])
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                lat_input = st.number_input("Latitud", format="%.6f", value=0.0)
            with col_c2:
                lon_input = st.number_input("Longitud", format="%.6f", value=0.0)
                
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                pisos_input = st.number_input("Cantidad de pisos", min_value=0, value=1)
            with col_p2:
                sub_input = st.number_input("Cantidad de subsuelos", min_value=0, value=0)
                
            horario_input = st.text_input("Horario de funcionamiento")
            obs_input = st.text_area("Observaciones de seguridad")
            
            st.divider()
            
            # 3. Botón de Verificación
            btn_verificar = st.form_submit_button("Verificar Objetivo y Consultar Entorno", use_container_width=True)

        # Si se apretó el botón de verificación, guardamos y mostramos los resultados abajo
        if btn_verificar:
            if nombre_input and direccion_input:
                conn = sqlite3.connect("sppro.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO edificios (nombre, tipo, direccion, altura, latitud, longitud, pisos, subsuelos, horario, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (nombre_input, tipo_input, direccion_input, altura_input, lat_input, lon_input, pisos_input, sub_input, horario_input, obs_input))
                conn.commit()
                cursor.execute("SELECT last_insert_rowid()")
                nuevo_id = cursor.fetchone()[0]
                conn.close()
                
                st.success(f"¡Objetivo '{nombre_input}' verificado y registrado con éxito!")
                st.session_state["objetivo_activo_id"] = nuevo_id
            else:
                st.error("El nombre y la dirección son obligatorios para realizar la verificación.")

        # Si hay un objetivo verificado activo en la sesión, mostramos Puntos de Apoyo, Clima y Generador de PDF
        if "objetivo_activo_id" in st.session_state:
            act_id = st.session_state["objetivo_activo_id"]
            
            conn = sqlite3.connect("sppro.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM edificios WHERE id = ?", (act_id,))
            obj_row = cursor.fetchone()
            conn.close()

            if obj_row:
                st.markdown("---")
                st.info(f"📋 *Resultado de la Verificación para:* {obj_row[1]} ({obj_row[3]})")

                # Mostrar Puntos de Apoyo
                st.subheader("Puntos de Apoyo Cercanos / Disponibles")
                conn_p = sqlite3.connect("sppro.db")
                df_pa = pd.read_sql("SELECT tipo, nombre, direccion, observaciones FROM puntos_apoyo", conn_p)
                conn_p.close()
                
                if not df_pa.empty:
                    st.dataframe(df_pa, use_container_width=True)
                else:
                    st.warning("No hay puntos de apoyo cargados en el sistema actualmente.")

                # Mostrar Clima
                st.subheader("Condiciones Meteorológicas Actuales")
                datos_clima = clima.obtener_clima()
                if datos_clima:
                    cl1, cl2, cl3 = st.columns(3)
                    with cl1:
                        st.metric("Temperatura", datos_clima["temperatura"])
                        st.metric("Cielo", datos_clima["estado"])
                    with cl2:
                        st.metric("Viento", datos_clima["viento"])
                        st.metric("Humedad", datos_clima["humedad"])
                    with cl3:
                        st.metric("Presión", datos_clima["presion"])
                else:
                    st.warning("Información meteorológica no disponible.")

                st.markdown("---")

                # Botón para generar el PDF
                st.subheader("Generación de Informe")
                if st.button("Generar y Descargar PDF del Objetivo", type="primary", use_container_width=True):
                    pdf = PDFReporte()
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(0, 51, 102)
                    
                    pdf.cell(0, 8, limpiar_texto("IDENTIFICACION DEL OBJETIVO"), ln=True)
                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 6, limpiar_texto(f"Nombre: {obj_row[1]}"), ln=True)
                    pdf.cell(0, 6, limpiar_texto(f"Tipo: {obj_row[2]}"), ln=True)
                    pdf.cell(0, 6, limpiar_texto(f"Direccion: {obj_row[3]} (Altura: {obj_row[4]})"), ln=True)
                    pdf.cell(0, 6, limpiar_texto(f"Coordenadas: Lat: {obj_row[5]}, Lon: {obj_row[6]}"), ln=True)
                    pdf.cell(0, 6, limpiar_texto(f"Pisos: {obj_row[7]} | Subsuelos: {obj_row[8]}"), ln=True)
                    pdf.cell(0, 6, limpiar_texto(f"Horario: {obj_row[9]}"), ln=True)
                    pdf.ln(4)
                    
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(0, 51, 102)
                    pdf.cell(0, 8, limpiar_texto("CONDICIONES METEOROLOGICAS"), ln=True)
                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(0, 0, 0)
                    if datos_clima:
                        pdf.cell(0, 6, limpiar_texto(f"Temperatura: {datos_clima['temperatura']} | Estado: {datos_clima['estado']}"), ln=True)
                        pdf.cell(0, 6, limpiar_texto(f"Viento: {datos_clima['viento']} | Humedad: {datos_clima['humedad']} | Presion: {datos_clima['presion']}"), ln=True)
                    else:
                        pdf.cell(0, 6, limpiar_texto("Informacion meteorologica no disponible."), ln=True)
                    pdf.ln(4)

                    if not df_pa.empty:
                        pdf.set_font("Arial", "B", 12)
                        pdf.set_text_color(0, 51, 102)
                        pdf.cell(0, 8, limpiar_texto("PUNTOS DE APOYO"), ln=True)
                        pdf.set_font("Arial", "", 10)
                        pdf.set_text_color(0, 0, 0)
                        for _, row_pa in df_pa.iterrows():
                            pdf.cell(0, 6, limpiar_texto(f"[{row_pa['tipo']}] {row_pa['nombre']} - {row_pa['direccion']} ({row_pa['observaciones']})"), ln=True)
                        pdf.ln(4)

                    if obj_row[10]:
                        pdf.set_font("Arial", "B", 12)
                        pdf.set_text_color(0, 51, 102)
                        pdf.cell(0, 8, limpiar_texto("OBSERVACIONES"), ln=True)
                        pdf.set_font("Arial", "", 10)
                        pdf.set_text_color(0, 0, 0)
                        pdf.multi_cell(0, 6, limpiar_texto(obj_row[10]))

                    pdf_bytes = pdf.output(dest="S").encode("latin-1")
                    st.download_button(
                        label="Descargar Archivo PDF Final",
                        data=pdf_bytes,
                        file_name=f"Informe_SPPRO_{obj_row[1].replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )

    with tab_hist:
        st.subheader("Historial de Edificios Verificados")
        conn = sqlite3.connect("sppro.db")
        df_edificios = pd.read_sql("SELECT * FROM edificios", conn)
        conn.close()
        
        if df_edificios.empty:
            st.info("No hay objetivos registrados todavía.")
        else:
            st.dataframe(df_edificios, use_container_width=True)

# ==========================================
# SECCIÓN 2: PUNTOS DE APOYO
# ==========================================
elif seccion == "Puntos de Apoyo":
    st.header("Puntos de Apoyo")
    
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
                    st.success("Punto de apoyo registrado con éxito.")
                else:
                    st.error("El nombre es obligatorio.")
                    
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
elif seccion == "Clima":
    st.header("Condiciones Meteorológicas")
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
        st.warning("Información meteorológica no disponible.")

# ==========================================
# SECCIÓN 4: GESTIÓN DE USUARIOS
# ==========================================
elif seccion == "Gestion de Usuarios":
    if st.session_state["user_role"] != "Administrador":
        st.error("Acceso denegado.")
        st.stop()
        
    st.header("Gestion de Usuarios")
    
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
                    st.success("Usuario creado exitosamente.")
                    st.rerun()
                except:
                    st.error("El usuario ya existe.")
            else:
                st.warning("Complete los campos.")

    st.divider()
    st.subheader("Usuarios Registrados")
    conn = sqlite3.connect("sppro.db")
    df_users = pd.read_sql("SELECT username, activo, rol FROM usuarios", conn)
    conn.close()
    
    for _, row in df_users.iterrows():
        cols = st.columns([2, 1, 1, 1])
        cols[0].write(row["username"])
        cols[1].write(row["rol"])
        cols[2].write("Activo" if row["activo"] == 1 else "Inactivo")
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
                    conn.cursor().execute("UPDATE usuarios SET activo = 1 WHERE username = ?", (row["username"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
