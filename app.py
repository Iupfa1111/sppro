import datetime
import sqlite3
import pandas as pd
import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="SPPRO by Angel Ibañez", layout="wide")

# ==========================================
# 1. BASE DE DATOS INTELIGENTE Y AUTOREPARABLE
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
    
    # Asegurar de forma segura que la columna privado exista siempre desde el inicio
    cursor.execute("PRAGMA table_info(edificios)")
    columnas = [info[1] for info in cursor.fetchall()]
    if "privado" not in columnas:
        cursor.execute("ALTER TABLE edificios ADD COLUMN privado INTEGER NOT NULL DEFAULT 0")
        
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("admin", "admin123", 1, "Administrador"))
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", ("operador1", "user123", 1, "Operador"))
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. DICCIONARIO INTELIGENTE: LUGARES, DATOS AMBIENTALES Y PUNTOS SEGUROS
# ==========================================
BASE_CONOCIMIENTO = {
    "Congreso de la Nación": {
        "direccion": "Av. Rivadavia 1864, CABA",
        "clima": "☀️ Despejado / 21°C / Viento SE a 12 km/h",
        "altura": "25 msnm",
        "hospitales": ["Hospital General de Agudos B. Rivadavia (Av. Las Heras 2670)", "Hospital Ramos Mejía (Urquiza 609)"],
        "comisarias": ["Comisaría Vecinal 3B (Pasco 473)", "Comisaría Vecinal 1B (Av. de Mayo 1269)"]
    },
    "Hotel Hilton": {
        "direccion": "Macacha Güemes 351, Puerto Madero, CABA",
        "clima": "⛅ Parcialmente nublado / 22°C / Viento Este a 15 km/h",
        "altura": "8 msnm",
        "hospitales": ["Hospital General de Agudos Dr. C. Argerich (Pi y Margall 750)"],
        "comisarias": ["Comisaría Vecinal 1E (Av. Belgrano 340)"]
    },
    "Casa Rosada": {
        "direccion": "Balcarce 50, CABA",
        "clima": "☀️ Despejado / 21°C / Viento SE a 12 km/h",
        "altura": "10 msnm",
        "hospitales": ["Hospital Argerich (Pi y Margall 750)", "Hospital Santa Lucía (Av. San Juan 2021)"],
        "comisarias": ["Comisaría Vecinal 1D (Av. Belgrano 340)"]
    },
    "Teatro Colón": {
        "direccion": "Cerrito 628, CABA",
        "clima": "☀️ Despejado / 21°C / Viento Este a 14 km/h",
        "altura": "22 msnm",
        "hospitales": ["Hospital General de Agudos B. Rivadavia (Av. Las Heras 2670)"],
        "comisarias": ["Comisaría Vecinal 1A (Suipacha 1156)"]
    },
    "Palacio Barolo": {
        "direccion": "Av. de Mayo 1370, CABA",
        "clima": "☀️ Despejado / 21°C / Viento SE a 12 km/h",
        "altura": "24 msnm",
        "hospitales": ["Hospital Ramos Mejía (Urquiza 609)", "Hospital Santa Lucía (Av. San Juan 2021)"],
        "comisarias": ["Comisaría Vecinal 1B (Av. de Mayo 1269)"]
    },
    "Hotel Alvear": {
        "direccion": "Av. Alvear 1891, Recoleta, CABA",
        "clima": "⛅ Parcialmente nublado / 20°C / Viento Este a 10 km/h",
        "altura": "26 msnm",
        "hospitales": ["Hospital Fernán Pérez de Quirno / Fernández (Cerviño 3356)"],
        "comisarias": ["Comisaría Vecinal 2A (Av. Las Heras 1861)"]
    },
    "Sheraton Buenos Aires Hotel": {
        "direccion": "San Martín 1225, Retiro, CABA",
        "clima": "☀️ Despejado / 21°C / Viento Este a 15 km/h",
        "altura": "12 msnm",
        "hospitales": ["Hospital Fernández (Cerviño 3356)"],
        "comisarias": ["Comisaría Vecinal 1A (Suipacha 1156)"]
    },
    "Luna Park": {
        "direccion": "Av. Madero 420, CABA",
        "clima": "☀️ Despejado / 21°C / Viento Este a 15 km/h",
        "altura": "11 msnm",
        "hospitales": ["Hospital Argerich (Pi y Margall 750)"],
        "comisarias": ["Comisaría Vecinal 1A (Suipacha 1156)"]
    }
}

# ==========================================
# 3. ESTADOS DE SESIÓN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None

if "resultado_busqueda" not in st.session_state:
    st.session_state["resultado_busqueda"] = None

# ==========================================
# 4. GENERADOR DE PDF
# ==========================================
def generar_pdf_evento(edificio, direccion, fecha_hora, clima, altura, accesos, hospitales, comisarias):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="SPPRO - REPORTE DE VERIFICACIÓN DE EDIFICIO", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt="Sistema de Seguridad Patrimonial by Angel Ibañez", ln=True, align="C")
    pdf.line(10, 25, 200, 25)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="1. Datos del Evento y Contexto Geográfico", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 6, txt=f"- Edificio / Sitio: {edificio}", ln=True)
    pdf.cell(200, 6, txt=f"- Dirección: {direccion}", ln=True)
    pdf.cell(200, 6, txt=f"- Fecha y Hora: {fecha_hora}", ln=True)
    pdf.cell(200, 6, txt=f"- Clima y Viento: {clima}", ln=True)
    pdf.cell(200, 6, txt=f"- Altura sobre el nivel del mar: {altura}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="2. Detalle de Entradas, Salidas y Seguridad", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 6, txt=accesos)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 8, txt="3. Puntos Seguros Cercanos Automáticos", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 6, txt=f"Hospitales: {', '.join(hospitales)}\nComisarías: {', '.join(comisarias)}")
    
    pdf.ln(15)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 6, txt="Firma Operador a Cargo: ________", ln=True)
    
    return pdf.output(dest="S").encode("latin1")

# ==========================================
# 5. LOGIN
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
# SECCIÓN 1: VERIFICACIÓN, BÚSQUEDA Y REGISTRO
# ==========================================
if seccion == "🏢 Verificación de Edificios":
    st.header("🏢 Verificación Inteligente de Edificios y Entorno")
    
    tab_reg, tab_cons = st.tabs(["🔍 Buscar y Verificar Edificio", "📋 Historial y Reportes PDF"])
    
    with tab_reg:
        st.markdown("### 🏛️ Selección del Lugar")
        tipo_ingreso = st.radio("Método de selección:", ["Edificio / Hotel de renombre (Automático)", "Ingresar dirección / edificio personalizado"])
        
        if tipo_ingreso == "Edificio / Hotel de renombre (Automático)":
            nombre_seleccionado = st.selectbox("Seleccione el sitio conocido:", list(BASE_CONOCIMIENTO.keys()))
            nombre_edf = nombre_seleccionado
            datos_sitio = BASE_CONOCIMIENTO[nombre_seleccionado]
            direccion_edf = datos_sitio["direccion"]
            clima_automatico = datos_sitio["clima"]
            altura_automatica = datos_sitio["altura"]
            hospitales_auto = datos_sitio["hospitales"]
            comisarias_auto = datos_sitio["comisarias"]
        else:
            nombre_edf = st.text_input("Nombre del Edificio / Sitio")
            direccion_edf = st.text_input("Dirección exacta")
            clima_automatico = "☀️ Despejado / 21°C / Viento SE a 12 km/h"
            altura_automatica = "20 msnm"
            hospitales_auto = ["Hospital General más cercano (Ver sección Puntos Seguros)"]
            comisarias_auto = ["Comisaría de la jurisdicción local"]

        st.divider()

        col_b1, col_b2 = st.columns([1, 3])
        with col_b1:
            btn_buscar = st.button("🔍 Buscar / Verificar", use_container_width=True)
            
        if btn_buscar:
            if nombre_edf:
                st.session_state["resultado_busqueda"] = {
                    "nombre": nombre_edf,
                    "direccion": direccion_edf,
                    "clima": clima_automatico,
                    "altura": altura_automatica,
                    "hospitales": hospitales_auto,
                    "comisarias": comisarias_auto
                }
                st.success("✅ Verificación preliminar realizada con éxito (Sin guardar).")
            else:
                st.warning("⚠️ Indique o seleccione un edificio antes de buscar.")

        if st.session_state["resultado_busqueda"]:
            res = st.session_state["resultado_busqueda"]
            st.markdown("### 📊 Datos Ambientales y Puntos Seguros Encontrados")
            
            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.info(f"📍 *Sitio:* {res['nombre']}\n\n🏠 *Dirección:* {res['direccion']}\n\n🌤️ *Clima y Viento:* {res['clima']}\n\n⛰️ *Altura sobre el nivel del mar:* {res['altura']}")
            with c_info2:
                st.warning(f"🏥 *Hospitales Cercanos:\n" + "\n".join([f"- {h}" for h in res['hospitales']]) + f"\n\n👮 **Comisarías Cercanas:*\n" + "\n".join([f"- {c}" for c in res['comisarias']]))

        st.divider()
        
        with st.form("form_guardar_verificacion"):
            st.markdown("### 🚪 Registro Oficial y Accesos")
            accesos_edf = st.text_area("Detallar accesos principales, salidas de emergencia, portones y zonas vulnerables:")
            
            st.markdown("### 📷 Soporte Visual")
            st.file_uploader("Subir foto o captura de Google Maps", type=["jpg", "png", "jpeg"])
            es_privado = st.checkbox("🔒 Marcar como Edificio Privado (Acceso restringido)")
            
            btn_guardar = st.form_submit_button("💾 Guardar en el Historial")
            
            if btn_guardar:
                if nombre_edf and direccion_edf:
                    conn = sqlite3.connect("sppro.db")
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO edificios (nombre, direccion, accesos, imagen_path, privado) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (nombre_edf, direccion_edf, accesos_edf, "Imagen adjunta", 1 if es_privado else 0))
                    
                    fecha_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO eventos_historial (fecha_hora, edificio, clima, altura_snm, observaciones) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (fecha_str, nombre_edf, clima_automatico, altura_automatica, accesos_edf))
                    
                    conn.commit()
                    conn.close()
                    st.success("✅ Verificación guardada correctamente en la base de datos y disponible para reporte PDF.")
                else:
                    st.error("⚠️ Complete los datos del edificio antes de guardar.")

    with tab_cons:
        st.subheader("📋 Historial de Edificios y Generación de Reportes PDF")
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        
        # Consulta segura garantizada sin ALTER TABLE en medio de la lectura
        cursor.execute("SELECT id, nombre, direccion, accesos, privado FROM edificios")
        edificios_lista = cursor.fetchall()
        conn.close()
        
        if edificios_lista:
            for edf_id, nombre, direccion, accesos, privado in edificios_lista:
                with st.expander(f"🏢 {nombre} - {direccion} ({'Privado' if privado else 'Público'})"):
                    st.write(f"*Dirección:* {direccion}")
                    st.write(f"*Accesos y Salidas:* {accesos}")
                    
                    datos_extra = BASE_CONOCIMIENTO.get(nombre, {
                        "clima": "☀️ Despejado / 21°C", 
                        "altura": "20 msnm", 
                        "hospitales": ["Hospital General cercano"], 
                        "comisarias": ["Comisaría local"]
                    })
                    
                    # Generación directa y estable del PDF y botón de descarga dentro del expander
                    fecha_rep = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pdf_bytes = generar_pdf_evento(
                        nombre, 
                        direccion,
                        fecha_rep, 
                        datos_extra["clima"], 
                        datos_extra["altura"], 
                        accesos or "Sin detalles de accesos registrados",
                        datos_extra["hospitales"],
                        datos_extra["comisarias"]
                    )
                    
                    st.download_button(
                        label=f"⬇️ Descargar Reporte PDF - {nombre}",
                        data=pdf_bytes,
                        file_name=f"Reporte_Edificio_{nombre.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{edf_id}"
                    )
        else:
            st.info("No hay edificios registrados todavía en el historial.")

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
        st.write("• *Hospital General de Agudos Dr. C. Argerich* - Pi y Margall 750, CABA")

    with tab_com:
        st.markdown("### Dependencias Policiales")
        st.write("• *Comisaría Vecinal 1A (Policía de la Ciudad)* - Suipacha 1156, CABA")
        st.write("• *Comisaría Vecinal 2B* - Las Heras y Pueyrredón, CABA")
        st.write("• *Comisaría Vecinal 3B* - Pasco 473, CABA")

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
