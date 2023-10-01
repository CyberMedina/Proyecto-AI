from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from urllib.parse import urlencode #Dependencia utilizada para redirigir al modal de inicio de sesión
import urllib.parse 
from config import connectionBD


app = Flask(__name__)

def in_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id"):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def login_requiredUser_system(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("usersis_id") is None:
            return redirect(url_for('login_system'))
        return f(*args, **kwargs)
    return decorated_function



def obtener_detalles_productos(producto_ids):
    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    
    # Crear la consulta SQL
    placeholders = ', '.join(['%s'] * len(producto_ids))
    sql = f"SELECT * FROM productos WHERE id_producto IN ({placeholders})"
    
    cursor.execute(sql, producto_ids)
    productos = cursor.fetchall()
    
    cursor.close()
    return productos
