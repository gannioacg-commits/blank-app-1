# app.py
import streamlit as st
import sqlite3
import os
from datetime import datetime

# ================= CONFIG =================
DB_PATH = "facturas.db"
PDF_DIR = "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

# ================= ESTILOS =================
st.set_page_config(page_title="Gestor de Facturas", layout="centered")

st.markdown("""
<style>
:root {
    --green: #1f8f4c;
    --green-dark: #166b39;
}

.stApp {
    background-color: #f6f9f7;
}

header {visibility: hidden;}

.title {
    font-size: 28px;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 25px;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 14px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.stButton > button {
    background-color: var(--green);
    color: white;
    border-radius: 10px;
    height: 48px;
    font-weight: 600;
    border: none;
}

.stButton > button:hover {
    background-color: var(--green-dark);
}
</style>
""", unsafe_allow_html=True)

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

# ================= HEADER =================
st.image(
    "https://dummyimage.com/1200x200/1f8f4c/ffffff&text=ATHENS+CHEMICAL+GROUP",
    use_container_width=True
)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="title">Gestor de Descarga de Facturas de Proveedores</div>', unsafe_allow_html=True)

# ================= PROVEEDOR =================
proveedores = cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre").fetchall()
proveedor_nombres = [p[0] for p in proveedores]

proveedor = st.selectbox(
    "Proveedor",
    options=[""] + proveedor_nombres,
    placeholder="Seleccione un proveedor existente"
)

nuevo = st.text_input("O crear nuevo proveedor")
if nuevo:
    try:
        cursor.execute("INSERT INTO proveedores (nombre) VALUES (?)", (nuevo,))
        conn.commit()
        proveedor = nuevo
        st.success("Proveedor creado")
    except sqlite3.IntegrityError:
        st.warning("El proveedor ya existe")

# ================= FACTURA =================
descripcion = st.text_input("Descripción de la factura")

meses = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
    "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
    "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
}

col1, col2 = st.columns(2)
with col1:
    mes_nombre = st.selectbox("Mes", list(meses.keys()))
with col2:
    anio = st.selectbox("Año", list(range(2020, datetime.now().year + 1)))

pdf = st.file_uploader("Archivo PDF", type=["pdf"])

if st.button("Guardar en la base de datos"):
    if proveedor and descripcion and pdf:
        prov_id = cursor.execute(
            "SELECT id FROM proveedores WHERE nombre=?", (proveedor,)
        ).fetchone()[0]

        filename = f"{proveedor}_{anio}_{meses[mes_nombre]}_{pdf.name}".replace(" ", "_")
        path = os.path.join(PDF_DIR, filename)

        with open(path, "wb") as f:
            f.write(pdf.read())

        cursor.execute(
            """
            INSERT INTO facturas (proveedor_id, descripcion, mes, anio, pdf_path, fecha_carga)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (prov_id, descripcion, meses[mes_nombre], anio, path, datetime.now().isoformat())
        )
        conn.commit()
        st.success("Factura guardada correctamente")
    else:
        st.error("Completá todos los campos")

st.markdown('</div>', unsafe_allow_html=True)

# ================= LISTADO =================
st.markdown("## 📂 Facturas cargadas")
rows = cursor.execute(
    """
    SELECT p.nombre, f.descripcion, f.mes, f.anio, f.pdf_path
    FROM facturas f
    JOIN proveedores p ON p.id = f.proveedor_id
    ORDER BY f.anio DESC, f.mes DESC
    """
).fetchall()

for r in rows:
    with st.expander(f"{r[0]} – {r[1]} ({r[2]}/{r[3]})"):
        with open(r[4], "rb") as file:
            st.download_button("Descargar PDF", file, file_name=os.path.basename(r[4]))
