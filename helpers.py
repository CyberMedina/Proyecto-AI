from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from urllib.parse import urlencode #Dependencia utilizada para redirigir al modal de inicio de sesión
import urllib.parse 
from config import connectionBD
import os
import datetime
import requests
import dropbox
import pytz


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

def obtener_enlace_descarga(dbx, file_path):
    """Genera un enlace de descarga para el archivo de Dropbox, reutilizando el existente si ya existe"""
    try:
        # Verificar si ya existe un enlace compartido
        shared_links = dbx.sharing_list_shared_links(path=file_path, direct_only=True).links
        if shared_links:
            shared_link_metadata = shared_links[0]
        else:
            shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
        
        return shared_link_metadata.url.replace("?dl=0", "?dl=1")
    except dropbox.exceptions.ApiError as e:
        print(f"Error creating or retrieving shared link: {e}")
        return None
    
def obtener_str_fecha_hora():
    """Obtiene la fecha y hora actual en formato de cadena"""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def get_latest_sql_file(dbx, folder_path):
    # Listar todos los archivos en la carpeta
    response = dbx.files_list_folder(folder_path)
    file_list = response.entries
    
    # Filtrar solo archivos .sql
    sql_files = [file for file in file_list if file.name.endswith('.sql')]
    
    # Ordenar los archivos por fecha de modificación (más reciente primero)
    sql_files.sort(key=lambda x: x.client_modified, reverse=True)
    
    # Retornar el archivo más reciente, si existe
    if sql_files:
        return sql_files[0]
    else:
        return None

def get_all_sql_files(dbx, folder_path):
    # Listar todos los archivos en la carpeta
    response = dbx.files_list_folder(folder_path)
    file_list = response.entries
    
    # Filtrar solo archivos .sql
    sql_files = [file for file in file_list if file.name.endswith('.sql')]
    
    # Ordenar los archivos por fecha de modificación (más reciente primero)
    sql_files.sort(key=lambda x: x.client_modified, reverse=True)
    
    return sql_files if sql_files else None


def get_most_recent_sql_file(dbx, folder_path):
    """
    Retorna el archivo SQL más reciente de una carpeta en Dropbox.
    
    Args:
        dbx: Instancia de Dropbox
        folder_path: Ruta de la carpeta a buscar
        
    Returns:
        El archivo SQL más reciente o None si no hay archivos SQL
    """
    try:
        # Listar todos los archivos en la carpeta
        response = dbx.files_list_folder(folder_path)
        
        # Filtrar y obtener el archivo SQL más reciente
        sql_files = [file for file in response.entries if file.name.lower().endswith('.sql')]
        if not sql_files:
            return None
            
        return max(sql_files, key=lambda x: x.client_modified)
        
    except Exception as e:
        print(f"Error al obtener el archivo SQL más reciente: {e}")
        return None
def get_most_recent_sql_file(dbx, folder_path):
    """
    Retorna el archivo SQL más reciente de una carpeta en Dropbox.
    
    Args:
        dbx: Instancia de Dropbox
        folder_path: Ruta de la carpeta a buscar
        
    Returns:
        El archivo SQL más reciente o None si no hay archivos SQL
    """
    try:
        # Listar todos los archivos en la carpeta
        response = dbx.files_list_folder(folder_path)
        
        # Filtrar y obtener el archivo SQL más reciente
        sql_files = [file for file in response.entries if file.name.lower().endswith('.sql')]
        if not sql_files:
            return None
            
        return max(sql_files, key=lambda x: x.client_modified)
        
    except Exception as e:
        print(f"Error al obtener el archivo SQL más reciente: {e}")
        return None
    
def obtener_enlace_descarga(dbx, file_path):
    """Genera un enlace de descarga para el archivo de Dropbox, reutilizando el existente si ya existe"""
    try:
        # Verificar si ya existe un enlace compartido
        shared_links = dbx.sharing_list_shared_links(path=file_path, direct_only=True).links
        if shared_links:
            shared_link_metadata = shared_links[0]
        else:
            shared_link_metadata = dbx.sharing_create_shared_link_with_settings(file_path)
        
        return shared_link_metadata.url.replace("?dl=0", "?dl=1")
    except dropbox.exceptions.ApiError as e:
        print(f"Error creating or retrieving shared link: {e}")
        return None
    
def obtener_str_fecha_hora():
    """Obtiene la fecha y hora actual en formato de cadena"""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def convertir_fecha(fecha, zona_horaria_local='America/Managua'):
    """Convierte la fecha del servidor a la hora local en un formato más legible"""
    # Zona horaria del servidor (asumido como UTC)
    server_timezone = pytz.utc
    
    # Zona horaria local
    local_timezone = pytz.timezone(zona_horaria_local)
    
    # Localizar la fecha del servidor
    server_time_with_tz = server_timezone.localize(fecha)
    
    # Convertir a la zona horaria local
    local_time = server_time_with_tz.astimezone(local_timezone)
    
    # Formatear la fecha y hora en el formato deseado sin AM/PM
    fecha_formateada = local_time.strftime("%A %d de %B de %Y a las %I:%M:%S")
    
    # Capitalizar el primer carácter de la cadena formateada para una mejor presentación
    fecha_formateada = fecha_formateada.capitalize()
    
    # Añadir manualmente el formato de AM/PM en español
    hora = local_time.hour
    if hora < 12:
        am_pm = "am"
    else:
        am_pm = "pm"
    
    # Agregar AM/PM a la fecha formateada
    fecha_formateada += f" {am_pm}"
    
    return fecha_formateada

# Función para subir archivo a Dropbox
def upload_to_dropbox(dbx, file, dropbox_destination_path):
    """Sube el archivo a Dropbox y devuelve el enlace compartido."""
    try:
        file.seek(0)  # Asegurarse de que el puntero de lectura del archivo esté al inicio
        dbx.files_upload(file.read().encode('utf-8'), dropbox_destination_path)
        
        # Crear y obtener el enlace compartido
        shared_link = dbx.sharing_create_shared_link(dropbox_destination_path)
        download_url = shared_link.url.replace('?dl=0', '?dl=1')  # Convertir a enlace de descarga directa
        
        return True, None, download_url
    except Exception as e:
        return False, str(e), None
    
    
def obtener_str_fecha_hora():
    """Obtiene la fecha y hora actual en formato de cadena"""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

