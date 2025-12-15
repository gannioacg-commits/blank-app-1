# app.py
import streamlit as st
import sqlite3
import os
from datetime import datetime

# ================= CONFIG =================
DB_PATH = "facturas.db"
PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

# ================= DB =================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_conn()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER,
    descripcion TEXT,
    mes INTEGER,
    anio INTEGER,
    pdf_path TEXT,
    fecha_carga TEXT,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
)
""")
conn.commit()

# ================= UI =================
st.title("📄 Gestor de Facturas PDF")

# --- Proveedor ---
st.subheader("Proveedor")
proveedores = cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre").fetchall()
proveedor_nombres = [p[0] for p in proveedores]

opcion = st.radio("Proveedor", ["Seleccionar existente", "Crear nuevo"])

if opcion == "Crear nuevo":
    proveedor = st.text_input("Nombre del proveedor")
    if st.button("Crear proveedor") and proveedor:
        try:
            cursor.execute("INSERT INTO proveedores (nombre) VALUES (?)", (proveedor,))
            conn.commit()
            st.success("Proveedor creado")
        except sqlite3.IntegrityError:
            st.error("El proveedor ya existe")
else:
    proveedor = st.selectbox("Seleccionar proveedor", proveedor_nombres)

# --- Factura ---
st.subheader("Datos de la factura")
descripcion = st.text_input("Descripción")
mes = st.selectbox("Mes", list(range(1, 13)))
anio = st.selectbox("Año", list(range(2020, datetime.now().year + 1)))
pdf = st.file_uploader("Adjuntar factura (PDF)", type=["pdf"])

if st.button("Guardar factura"):
    if proveedor and descripcion and pdf:
        prov_id = cursor.execute(
            "SELECT id FROM proveedores WHERE nombre=?", (proveedor,)
        ).fetchone()[0]

        filename = f"{proveedor}_{anio}_{mes}_{pdf.name}".replace(" ", "_")
        path = os.path.join(PDF_DIR, filename)

        with open(path, "wb") as f:
            f.write(pdf.read())

        cursor.execute(
            """
            INSERT INTO facturas (proveedor_id, descripcion, mes, anio, pdf_path, fecha_carga)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (prov_id, descripcion, mes, anio, path, datetime.now().isoformat())
        )
        conn.commit()
        st.success("Factura guardada correctamente")
    else:
        st.error("Completar todos los campos")

# --- Consulta ---
st.subheader("📂 Facturas cargadas")
rows = cursor.execute(
    """
    SELECT p.nombre, f.descripcion, f.mes, f.anio, f.pdf_path
    FROM facturas f
    JOIN proveedores p ON p.id = f.proveedor_id
    ORDER BY f.anio DESC, f.mes DESC
    """
).fetchall()

for r in rows:
    with st.expander(f"{r[0]} - {r[1]} ({r[2]}/{r[3]})"):
        with open(r[4], "rb") as file:
            st.download_button("Descargar PDF", file, file_name=os.path.basename(r[4]))
