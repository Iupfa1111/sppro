import datetime
import sqlite3
import pandas as pd
import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="SPPRO by Angel Ibañez", layout="wide")

# ==========================================
# BASE DE DATOS INTELIGENTE Y AUTOREPARABLE
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
            direccion TEXT NOT NULL,
            accesos TEXT,
            imagen_path TEXT,
            privado INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            edificio TEXT,
            clima TEXT,
            altura_snm TEXT,
            observaciones TEXT
        )
    """)
    
    # Blindaje ante tablas existentes sin columnas nuevas
    try:
        cursor.execute("ALTER TABLE edificios ADD COLUMN privado INTEGER NOT NULL DEFAULT 0")
    except:
        pass
        
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("admin", "admin123", 1, "Administrador"))
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("operador1", "user123", 1, "Operador"))
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# DICCIONARIO DE EDIFICIOS Y LUGARES DE RENOMBRE
# ==========================================
LUGARES_RENOMBRE = {
    "Congreso de la Nación": "Av. Rivadavia 1864, CABA",
    "Hotel Hilton": "Macacha Güemes 351, Puerto Madero, CABA",
    "Casa Rosada": "Balcarce 50, CABA",
    "Teatro Colón": "Cerrito 628, CABA",
    "Palacio Barolo": "Av. de Mayo 1370, CABA",
    "Hotel Alvear": "Av. Alvear 1891, Recoleta, CABA",
    "Sheraton Buenos Aires Hotel": "San Martín 1225, Retiro, CABA",
    "Luna Park": "Av. Madero 420, CABA",
    "Torre Monumental (De los Ingleses)": "Av. Dr. José María Ramos Mejía 1315, Retiro"
}

# ==========================================
# ESTADOS DE SESIÓN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None

# ==========================================
# GENERADOR DE PDF
# ==========================================
def generar_pdf_evento(edificio, direccion, fecha_hora, clima, altura, accesos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="SPPRO - REPORTE DE VERIFICACIÓN DE EDIFICIO", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt="Sistema de Seguridad Patrimonial by Angel Ibañez", ln=True, align="C")
    pdf.line(10, 25, 200, 25)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="1. Datos del Evento y Contexto", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt=f"- Edificio / Sitio: {edificio}", ln=True)
    pdf.cell(200, 6, txt=f"- Dirección: {direccion}", ln=True)
    pdf.cell(200, 6, txt=f"- Fecha y Hora: {fecha_hora}", ln=True)
    pdf.cell(200, 6, txt=f"- Condición Climática: {clima}", ln=True)
    pdf.cell(200, 6, txt=f"- Altura sobre el nivel del mar: {altura}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="2. Detalle de Entradas, Salidas y Seguridad", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 6, txt=accesos)
    
    pdf.ln(15)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 6, txt="Firma Operador a Cargo: ________", ln=True)
    
    return pdf.output(dest="S").encode("latin1")

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
# INTERFAZ PRINCIPAL
# ==========================================
st.title("SPPRO")
st.caption(f"by Angel Ibañez | Operador activo: {st.session_state['username']} ({st.session_state['user_role']})")

st.sidebar.title("Menú SPPRO")
opciones = ["🏢 Verificación de Edificios", "🏥 Puntos Seguros Cercanos", "👥 Gestión de Usuarios"]
seccion = st.sidebar.radio("Navegación:", opciones)

st.sidebar.divider()
st.sidebar.subheader("📤 Compartir Aplicación")
st.sidebar.text_input("Enlace de acceso rápido:", value="https://sppro-app.streamlit.app", disabled=True)
st.sidebar.caption("Copia este enlace para compartir la plataforma con otros operadores.")

if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    st.session_state["logged_in"] = False
    st.rerun()

# ==========================================
# SECCIÓN 1: EDIFICIOS, ENTRADAS Y SALIDAS
# ==========================================
if seccion == "🏢 Verificación de Edificios":
    st.header("🏢 Verificación de Edificios, Entradas y Salidas")
    
    tab_reg, tab_cons = st.tabs(["➕ Registrar / Verificar Edificio", "📋 Historial y Reportes PDF"])
    
    with tab_reg:
        with st.form("form_verif_edificio"):
            st.markdown("### 🏛️ Selección o Ingreso del Edificio / Hotel")
            
            # Selector inteligente de edificios conocidos
            tipo_ingreso = st.radio("¿Cómo desea identificar el lugar?", ["Seleccionar un edificio/hotel de renombre", "Ingresar nombre personalizado manualmente"])
            
            direccion_automatica = ""
            if tipo_ingreso == "Seleccionar un edificio/hotel de renombre":
                nombre_seleccionado = st.selectbox("Elija el punto conocido:", list(LUGARES_RENOMBRE.keys()))
                nombre_edf = nombre_seleccionado
                direccion_edf = LUGARES_RENOMBRE[nombre_seleccionado]
                st.info(f"📍 Dirección autocompletada por el sistema: *{direccion_edf}*")
            else:
                nombre_edf = st.text_input("Nombre / Código del Edificio")
                direccion_edf = st.text_input("Dirección y Localidad")
            
            st.markdown("### 🚪 Entradas, Salidas y Accesos")
            accesos_edf = st.text_area("Detallar accesos principales, salidas de emergencia, portones y zonas vulnerables:")
            
            st.markdown("### 📷 Soporte Visual y Documentación")
            st.radio("¿Cómo desea adjuntar la imagen de referencia?", ["Subir foto desde la cámara / dispositivo", "Cargar captura o imagen de Google Maps"])
            archivo_imagen = st.file_uploader("Seleccionar archivo de imagen", type=["jpg", "png", "jpeg"])
            
            st.markdown("### 📊 Datos Ambientales y Contextuales (Para el Reporte)")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                clima_actual = st.selectbox("Clima actual:", ["☀️ Despejado / Soleado", "⛅ Parcialmente nublado", "☁️ Nublado", "🌧️ Lluvia ligera / Moderada", "🌩️ Tormenta"])
            with col_d2:
                altura_snm = st.text_input("Altura sobre el nivel del mar (ej: 25 msnm)", value="25 msnm")
                
            es_privado = st.checkbox("🔒 Marcar como Edificio Privado (Acceso restringido)")
            
            if st.form_submit_button("Guardar y Registrar Verificación"):
                if nombre_edf and direccion_edf:
                    path_img = "Imagen cargada" if archivo_imagen else "Sin adjunto"
                    
                    conn = sqlite3.connect("sppro.db")
                    cursor = conn.cursor()
                    
                    # Asegurar estructura limpia en tiempo de ejecución
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS edificios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre TEXT NOT NULL,
                            direccion TEXT NOT NULL,
                            accesos TEXT,
                            imagen_path TEXT,
                            privado INTEGER NOT NULL DEFAULT 0
                        )
                    """)
                    
                    cursor.execute("INSERT INTO edificios (nombre, direccion, accesos, imagen_path, privado) VALUES (?, ?, ?, ?, ?)",
                                   (nombre_edf, direccion_edf, accesos_edf, path_img, 1 if es_privado else 0))
                    
                    fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO eventos_historial (fecha_hora, edificio, clima, altura_snm, observaciones) VALUES (?, ?, ?, ?, ?)",
                                   (fecha_str, nombre_edf, clima_actual, altura_snm, accesos_edf))
                    
                    conn.commit()
                    conn.close()
                    st.success("✅ Edificio verificado y registrado con éxito en el historial.")
                else:
                    st.error("⚠️ Complete o seleccione un edificio válido.")

    with tab_cons:
        st.subheader("📋 Edificios Registrados y Generación de Reportes")
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, direccion, accesos, privado FROM edificios")
        edificios_lista = cursor.fetchall()
        conn.close()
        
        if edificios_lista:
            for edf_id, nombre, direccion, accesos, privado in edificios_lista:
                with st.expander(f"🏢 {nombre} - {direccion} ({'Privado' if privado else 'Público'})"):
                    st.write(f"*Dirección:* {direccion}")
                    st.write(f"*Accesos y Salidas:* {accesos}")
                    
                    if st.button(f"📥 Generar Reporte PDF de {nombre}", key=f"pdf_{edf_id}"):
                        fecha_rep = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        pdf_bytes = generar_pdf_evento(
                            nombre, 
                            direccion,
                            fecha_rep, 
                            "Condición Normal / Registrada", 
                            "25 msnm", 
                            accesos
                        )
                        st.download_button(
                            label=f"⬇️ Descargar PDF - {nombre}",
                            data=pdf_bytes,
                            file_name=f"Reporte_Edificio_{nombre.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key=f"dl_{edf_id}"
                        )
        else:
            st.info("No hay edificios registrados todavía.")

# ==========================================
# SECCIÓN 2: PUNTOS SEGUROS CERCANOS
# ==========================================
elif seccion == "🏥 Puntos Seguros Cercanos":
    st.header("🏥 Puntos Seguros (Hospitales y Comisarías)")
    st.caption("Directorio de asistencia y recursos críticos cercanos para la operación de seguridad.")
    
    tab_hosp, tab_com = st.tabs(["🏥 Hospitales y Centros de Salud", "👮 Comisarías y Destacamentos"])
    
    with tab_hosp:
        st.markdown("### Centros Médicos de Urgencia")
        st.write("• *Hospital General de Agudos Dr. J. A. Fernández* - Cerviño 3356, CABA")
        st.write("• *Hospital General de Agudos B. Rivadavia* - Av. Las Heras 2670, CABA")
        st.write("• *Hospital Italiano de Buenos Aires* - Tte. Gral. Juan Domingo Perón 4190, CABA")
        st.write("• *Hospital San Martín* - Av. 1 y 70, La Plata")

    with tab_com:
        st.markdown("### Dependencias Policiales")
        st.write("• *Comisaría Vecinal 1A (Policía de la Ciudad)* - Suipacha 1156, CABA")
        st.write("• *Comisaría Vecinal 2B* - Las Heras y Pueyrredón, CABA")
        st.write("• *Comisaría Primera de La Plata* - Calle 53 entre 9 y 10, La Plata")

# ==========================================
# SECCIÓN 3: GESTIÓN DE USUARIOS
# ==========================================
elif seccion == "👥 Gestión de Usuarios":
    st.header("👥 Panel de Administración de Usuarios")
    
    if st.session_state["user_role"] != "Administrador":
        st.error("⛔ Acceso denegado. Solo los administradores pueden gestionar usuarios.")
        st.stop()
        
    st.subheader("Dar de Alta a Nuevo Usuario")
    with st.form("form_nuevo_usuario"):
        nuevo_user = st.text_input("Nombre de Usuario")
        nuevo_pass = st.text_input("Contraseña", type="password")
        nuevo_rol = st.selectbox("Rol del Usuario", ["Operador", "Administrador"])
        
        if st.form_submit_button("Crear Usuario"):
            if nuevo_user and nuevo_pass:
                try:
                    conn = sqlite3.connect("sppro.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios VALUES (?, ?, 1, ?)", (nuevo_user, nuevo_pass, nuevo_rol))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Usuario '{nuevo_user}' creado exitosamente.")
                    st.rerun()
                except:
                    st.error("❌ El nombre de usuario ya existe.")
            else:
                st.warning("⚠️ Complete todos los campos.")

    st.divider()
    st.subheader("Usuarios Registrados (Alta / Baja)")
    
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, activo, rol FROM usuarios")
    usuarios_db = cursor.fetchall()
    conn.close()
    
    for u, activo, rol in usuarios_db:
        col_u1, col_u2, col_u3 = st.columns([2, 1, 1])
        with col_u1:
            st.write(f"👤 *{u}* ({rol})")
        with col_u2:
            estado_texto = "🟢 Activo" if activo == 1 else "🔴 Inactivo"
            st.write(estado_texto)
        with col_u3:
            if u != "admin":
                if activo == 1:
                    if st.button("Dar de Baja", key=f"baja_{u}"):
                        conn = sqlite3.connect("sppro.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE usuarios SET activo = 0 WHERE username = ?", (u,))
                        conn.commit()
                        conn.close()
                        st.rerun()
                else:
                    if st.button("Dar de Alta", key=f"alta_{u}"):
                        conn = sqlite3.connect("sppro.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE usuarios SET activo = 1 WHERE username = ?", (u,))
                        conn.commit()
                        conn.close()
                        st.rerun()
