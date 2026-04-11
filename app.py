"""
Inventario PYME - Backend Flask
Requisitos: pip install flask flask-cors mysql-connector-python openpyxl
Uso: python app.py
"""

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
import mysql.connector
import openpyxl
import os
import random

app = Flask(__name__, static_folder="static")
app.secret_key = "super_secret_key_pyme"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)
CORS(app, supports_credentials=True)

# ── Configuración de base de datos (Dinámica) ─────────────────

def get_db():
    """Retorna una nueva conexión a MySQL usando datos de la sesión."""
    if "db_config" not in session:
        return None
    return mysql.connector.connect(**session["db_config"])

@app.route("/api/connect", methods=["POST"])
def connect_db():
    data = request.get_json()
    host = data.get("host", "localhost")
    user = data.get("user", "root")
    password = data.get("password", "")
    database = data.get("database", "pyme_db")

    try:
        # Intentar conectar
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        conn.close()
        # Si conecta, guardar en sesión
        session["db_config"] = {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
        return jsonify({"mensaje": "Conectado exitosamente"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 401

@app.route("/api/status", methods=["GET"])
def connection_status():
    if "db_config" in session:
        return jsonify({"connected": True})
    return jsonify({"connected": False}), 401
    
@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("db_config", None)
    return jsonify({"mensaje": "Desconectado"}), 200


# ── Rutas de la interfaz ────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ── API: Listar productos ───────────────────────────────────────
@app.route("/api/productos", methods=["GET"])
def listar_productos():
    conn = get_db()
    if not conn: return jsonify({"error": "No hay conexión a la base de datos"}), 401
    
    busqueda = request.args.get("q", "")
    cur = conn.cursor(dictionary=True)
    if busqueda:
        cur.execute(
            "SELECT * FROM productos WHERE nombre LIKE %s OR codigo LIKE %s ORDER BY id",
            (f"%{busqueda}%", f"%{busqueda}%")
        )
    else:
        cur.execute("SELECT * FROM productos ORDER BY id")
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(productos)


# ── API: Añadir producto individual ────────────────────────────
@app.route("/api/productos", methods=["POST"])
def agregar_producto():
    conn = get_db()
    if not conn: return jsonify({"error": "No hay conexión a la base de datos"}), 401
    
    data = request.get_json()
    codigo = str(data.get("codigo", "")).strip()
    nombre = str(data.get("nombre", "")).strip()
    precio = float(data.get("precio", 0))
    stock  = int(data.get("stock", 0))

    if not codigo or not nombre:
        return jsonify({"error": "Código y nombre son obligatorios"}), 400

    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO productos (codigo, nombre, precio, stock) VALUES (%s, %s, %s, %s)",
            (codigo, nombre, precio, stock)
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return jsonify({"id": new_id, "mensaje": f'Producto "{nombre}" añadido correctamente'}), 201
    except mysql.connector.errors.IntegrityError:
        cur.close()
        conn.close()
        return jsonify({"error": f'El código "{codigo}" ya existe'}), 409


# ── API: Editar producto ────────────────────────────────────────
@app.route("/api/productos/<int:producto_id>", methods=["PUT"])
def editar_producto(producto_id):
    conn = get_db()
    if not conn: return jsonify({"error": "No hay conexión a la base de datos"}), 401
    
    data = request.get_json()
    nombre = str(data.get("nombre", "")).strip()
    precio = float(data.get("precio", 0))
    stock  = int(data.get("stock", 0))

    if not nombre:
        return jsonify({"error": "El nombre no puede estar vacío"}), 400

    cur = conn.cursor()
    cur.execute(
        "UPDATE productos SET nombre=%s, precio=%s, stock=%s WHERE id=%s",
        (nombre, precio, stock, producto_id)
    )
    conn.commit()
    afectadas = cur.rowcount
    cur.close()
    conn.close()

    if afectadas == 0:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify({"mensaje": "Producto actualizado"})


# ── API: Eliminar producto ──────────────────────────────────────
@app.route("/api/productos/<int:producto_id>", methods=["DELETE"])
def eliminar_producto(producto_id):
    conn = get_db()
    if not conn: return jsonify({"error": "No hay conexión a la base de datos"}), 401
    
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
    conn.commit()
    afectadas = cur.rowcount
    cur.close()
    conn.close()

    if afectadas == 0:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify({"mensaje": "Producto eliminado"})


# ── API: Importar desde Excel ───────────────────────────────────
@app.route("/api/importar", methods=["POST"])
def importar_excel():
    conn = get_db()
    if not conn: return jsonify({"error": "No hay conexión a la base de datos"}), 401
    
    if "archivo" not in request.files:
        return jsonify({"error": "No se recibió ningún archivo"}), 400

    archivo = request.files["archivo"]
    if not archivo.filename.endswith((".xlsx", ".xls")):
        return jsonify({"error": "Solo se aceptan archivos .xlsx o .xls"}), 400

    try:
        wb   = openpyxl.load_workbook(archivo, data_only=True)
        hoja = wb.active
    except Exception:
        return jsonify({"error": "No se pudo leer el archivo Excel"}), 400

    cur  = conn.cursor()

    agregados  = 0
    duplicados = 0
    errores    = []

    for i, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), start=2):
        if not fila or (not fila[0] and not fila[1]):
            continue

        codigo = str(fila[0] or "").strip()
        nombre = str(fila[1] or "").strip()
        precio = float(fila[2] or 0) if fila[2] is not None else 0.0
        stock  = int(fila[3] or 0)   if fila[3] is not None else 0

        if not codigo or not nombre:
            errores.append(f"Fila {i}: código o nombre vacío")
            continue

        try:
            cur.execute(
                "INSERT INTO productos (codigo, nombre, precio, stock) VALUES (%s, %s, %s, %s)",
                (codigo, nombre, precio, stock)
            )
            agregados += 1
        except mysql.connector.errors.IntegrityError:
            duplicados += 1

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "agregados":  agregados,
        "duplicados": duplicados,
        "errores":    errores,
        "mensaje":    f"{agregados} productos importados, {duplicados} duplicados omitidos"
    })


# ── API: Estadísticas ───────────────────────────────────────────
@app.route("/api/estadisticas", methods=["GET"])
def estadisticas():
    conn = get_db()
    if not conn: return jsonify({"error": "No hay conexión"}), 401
    
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total, SUM(precio * stock) AS valor_total, SUM(CASE WHEN stock < 5 THEN 1 ELSE 0 END) AS stock_bajo FROM productos")
    stats = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({
        "total":       stats["total"] or 0,
        "valor_total": float(stats["valor_total"] or 0),
        "stock_bajo":  stats["stock_bajo"] or 0
    })

# ── API: Pronóstico ─────────────────────────────────────────────
@app.route("/api/pronostico", methods=["GET"])
def pronostico():
    conn = get_db()
    if not conn: return jsonify({"error": "No hay conexión"}), 401
    
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT codigo, nombre, precio, stock FROM productos")
    productos = cur.fetchall()
    cur.close()
    conn.close()
    
    # Simulate a forecast based on a simple algorithm (score = (100 / (stock+1)) * (1 + random variation) )
    # This identifies products that have low stock but are randomly picked up as "hot sellers"
    for p in productos:
        variacion_tendencia = random.uniform(0.8, 1.5)
        # Score calculation: lower stock = higher score, but modified by price to see "Best Sellers"
        # We will add a "demanda_estimada" metric
        p["demanda_estimada"] = int((100 / (p["stock"] + 1)) * variacion_tendencia * 10)
        p["score"] = p["demanda_estimada"] * p["precio"]

    # Sort by estimated demand
    productos_ordenados = sorted(productos, key=lambda x: x["demanda_estimada"], reverse=True)
    
    return jsonify({
        "recomendaciones": productos_ordenados[:10], # Top 10
        "todos": productos_ordenados
    })


if __name__ == "__main__":
    print("Servidor corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)
