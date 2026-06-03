import os
from flask import Flask, render_template, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
IMAGE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'imagenes')
DB_PATH = r"C:\Users\EMI\Desktop\GestionGratis_v1.6.2.0\Productos.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def obtener_ruta_imagen(producto_id):
    extensiones = ['.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
    for ext in extensiones:
        nombre_archivo = f"{producto_id}{ext}"
        if os.path.exists(os.path.join(IMAGE_FOLDER, nombre_archivo)):
            return nombre_archivo
    return None

@app.context_processor
def utility_processor():
    return dict(obtener_ruta_imagen=obtener_ruta_imagen)

@app.route('/')
@app.route('/categoria/<int:cat_id>')
def index(cat_id=None):
    fecha_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    db = get_db()
    categorias = db.execute("SELECT CategoriaId, Nombre FROM Categorias").fetchall()
    query = "SELECT ProductoId, Nombre, Precio, Stock, StockMinimo, Costo, FechaModificacion FROM Productos"
    params = ()
    if cat_id:
        query += " WHERE CategoriaId = ?"
        params = (cat_id,)
    productos = db.execute(query, params).fetchall()
    db.close()
    return render_template('index.html', productos=productos, categorias=categorias, fecha_limite=fecha_limite)

@app.route('/buscar')
def buscar():
    fecha_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    q = request.args.get('q', '').lower().strip()
    db = get_db()
    
    query = """
        SELECT DISTINCT p.ProductoId, p.Nombre, p.Precio, p.Stock, p.StockMinimo, p.Costo, FechaModificacion 
        FROM Productos p
        LEFT JOIN Referencias r ON p.ProductoId = r.ProductoId
        WHERE lower(p.Nombre) LIKE ? OR r.Valor LIKE ?
    """
    busqueda = f"%{q}%"
    productos = db.execute(query, (busqueda, busqueda)).fetchall()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        db.close()
        return render_template('productos_tabla.html', productos=productos, fecha_limite=fecha_limite)
    
    categorias = db.execute("SELECT CategoriaId, Nombre FROM Categorias").fetchall()
    db.close()
    return render_template('index.html', productos=productos, categorias=categorias, fecha_limite=fecha_limite)

@app.route('/alerta-stock')
def alerta_stock():
    fecha_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    db = get_db()
    categorias = db.execute("SELECT CategoriaId, Nombre FROM Categorias").fetchall()
    productos = db.execute("SELECT ProductoId, Nombre, Precio, Stock, StockMinimo, Costo, FechaModificacion FROM Productos WHERE Stock <= 5").fetchall()
    db.close()
    return render_template('index.html', productos=productos, categorias=categorias, fecha_limite=fecha_limite)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
