import datetime
import sqlite3
import pandas as pd
import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="SPPRO by Angel Ibañez", layout="wide")

# ==========================================
# 1. BASE DE DATOS INTELIGENTE
# ==========================================
def init_db():
    conn = sqlite3.connect("sppro.db")
    cursor = conn.cursor()
    
    # Crear tablas si no existen
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT NOT NULL, activo INTEGER NOT NULL, rol TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS edificios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, direccion TEXT NOT NULL, accesos TEXT, imagen_path TEXT, privado INTEGER NOT NULL DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS eventos_historial (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_hora TEXT, edificio TEXT, clima TEXT, altura_snm TEXT, observaciones TEXT)")
    
    # Verificación segura de columna privado
    cursor.execute("PRAGMA table_info(edificios)")
    columnas = [info[1] for info in cursor.fetchall()]
    if "privado" not in columnas:
        cursor.execute("ALTER TABLE edificios ADD COLUMN privado INTEGER NOT NULL DEFAULT 0")
        
    conn.commit()
    conn.close()

init_db()

# ... (El DICCIONARIO BASE_CONOCIMIENTO y la función generar_pdf_evento se mantienen igual que en tu original) ...
# [MANTÉN TUS FUNCIONES EXISTENTES AQUÍ]

# ==========================================
# SECCIÓN 1 (CORREGIDA): VERIFICACIÓN Y HISTORIAL
# ==========================================
if seccion == "🏢 Verificación de Edificios":
    # ... (Mantén tu código de búsqueda y guardado igual) ...

    with tab_cons:
        st.subheader("📋 Historial de Edificios y Generación de Reportes PDF")
        conn = sqlite3.connect("sppro.db")
        cursor = conn.cursor()
        
        # Consulta segura
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
                    
                    if st.button(f"📥 Generar Reporte PDF de {nombre}", key=f"pdf_{edf_id}"):
                        fecha_rep = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        pdf_bytes = generar_pdf_evento(
                            nombre, direccion, fecha_rep, datos_extra["clima"], 
                            datos_extra["altura"], accesos, datos_extra["hospitales"], 
                            datos_extra["comisarias"]
                        )
                        st.download_button(
                            label=f"⬇️ Descargar PDF - {nombre}",
                            data=pdf_bytes,
                            file_name=f"Reporte_Edificio_{nombre.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key=f"dl_{edf_id}"
                        )
        else:
            st.info("No hay edificios registrados todavía en el historial.")
