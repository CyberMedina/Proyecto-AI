import hashlib
import logging
import re
import requests
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, g
from flask_session import Session
from flask_mysqldb import MySQL, MySQLdb
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
# Dependencia utilizada para redirigir hacia modals
from urllib.parse import urlencode
from config import connectionBD
from helpers import in_session, login_requiredUser_system, obtener_detalles_productos
import os
import openai
from decimal import Decimal
from bs4 import BeautifulSoup
from flask_cors import cross_origin, CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from twilio.rest import Client
from heyoo import WhatsApp
import time
import json
import fitz
from pprint import pprint
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.llms.openai import OpenAI
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI


from odsclient import ODSClient


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# Se instancia la variable global para ser usada en jinja
app.jinja_env.globals['g'] = g


# No puuede ser cambiada esta función, ya que esta función es una palabra reservada
# Define una función para realizar tareas antes de cada solicitud
@app.before_request
def before_request():
    if 'usuariosClientesId' in session:
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT Nombres, Apellidos FROM usuarios_clientes WHERE usuariosClientesId = %s',
                       (session['usuariosClientesId'],))
        user_row = cursor.fetchone()
        cursor.close()

        primer_nombre = user_row['Nombres'].split(
        )[0] if user_row['Nombres'] else ''
        primer_apellido = user_row['Apellidos'].split(
        )[0] if user_row['Apellidos'] else ''

        g.user_id = session['usuariosClientesId']
        g.nombres = primer_nombre
        g.apellidos = primer_apellido

    if 'usersis_id' in session:
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT us.usersis_id, us.nombres, us.apellidos, us.correo, r.rolname FROM usuarios_sistema us JOIN rol r ON us.id_rol = r.id_rol WHERE us.usersis_id = %s', (session['usersis_id'],))
        user_row = cursor.fetchone()
        cursor.close()

        g.id_rol = session['usersis_id']
        g.nombres = user_row['nombres']
        g.apellidos = user_row['apellidos']
        g.correo = user_row['correo']
        g.rolname = user_row['rolname']

    # Establecer la sucursal predeterminada si no se ha seleccionado ninguna
    if 'sucursalId' not in session:
        session['sucursalId'] = 1

    # Obtener el nombre de la sucursal seleccionada
    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT nombre FROM sucursal WHERE sucursalId = %s', (session['sucursalId'],))
    g.sucursal_nombre = cursor.fetchone()['nombre']
    cursor.close()

    # Agrega aquí la lógica para obtener las categorías
    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id_categoria, nombre FROM categorias ORDER BY nombre ASC')
    categorias = cursor.fetchall()
    cursor.close()

    g.categorias = categorias  # Guarda las categorías en el objeto global g


# Con esta cosa estarán disponibles las variables en todas las plantillas yai
@app.context_processor
def inject_sucursal_nombre():
    return dict(sucursal_nombre=g.sucursal_nombre)


@app.context_processor
def inject_data():
    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT sucursalId, nombre, direccion_texto, direccion_maps, telefono FROM sucursal')
    sucursales = cursor.fetchall()
    cursor.close()
    db.close()
    return dict(sucursales=sucursales)


@app.after_request
def after_request(response):
    """Asegura que las respuestas del servidor no se almacenen en caché del navegador"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Actualiza el proyecto al realizar modificaciones en el HTML en la carpeta templates
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Esta es una forma de almacenar la información del usuario en el servidor para luego ser utilizada en la aplicación
# Configura la sesion para que no sea permanente y se cierre cuando se cierre el navegador
app.config["SESSION_PERMANENT"] = False
# Define el tipo de almacenamiento para las sesiones, utilizando el almacenamiento en el sistema de archivos del servidor
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():

    if request.method == 'GET':
        db = connectionBD()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
    SELECT 
        p.id_producto, 
        p.nombre AS nombre_producto, 
        p.descripcion, 
        p.precio, 
        u.nombre AS unidad_medida, 
        c.nombre AS categoria, 
        i.nombre_archivo, 
        i.ruta_archivo,
        inv.cantidad AS cantidad_inventario
    FROM productos p
    JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
    JOIN categorias c ON p.categoria_id = c.id_categoria
    LEFT JOIN imagenes i ON p.id_producto = i.producto_id
    JOIN inventario inv ON p.id_producto = inv.id_producto
    WHERE inv.sucursalId = %s
    ORDER BY p.nombre ASC
    LIMIT 8
""", (session['sucursalId'],))

        productosHome = cursor.fetchall()

        cursor.close()

        if 'sucursalId' not in session:
            session['sucursalId'] = 1

    # Obtener el nombre de la sucursal seleccionada
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT nombre FROM sucursal WHERE sucursalId = %s', (session['sucursalId'],))
        sucursal_nombre = cursor.fetchone()['nombre']
        cursor.close()

    return render_template('/index.html', categorias=g.categorias, productosHome=productosHome, sucursal_nombre=sucursal_nombre)


@app.route('/login_modal', methods=['GET'])
def login():
    # Lógica para determinar si se debe abrir el modal de inicio de sesión
    abrir_modal = True  # Puedes ajustar esta lógica según tus necesidades

    return render_template('index.html', abrir_modal=abrir_modal)


@app.route('/login_user', methods=['POST'])
def login_user():
    print("Petición recibida en /login_user")

    email = request.form['email']
    password = request.form['password']

    if not email or not password:
        return jsonify({'success': False, 'error': 'Debes completar todos los campos para continuar.'})

    # Verifica las credenciales en la base de datos
    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM usuarios_clientes WHERE correo = %s', (email,))
    user_row = cursor.fetchone()

    cursor.close()
    db.close()

    if user_row and check_password_hash(user_row['Contraseña'], password):
        session['usuariosClientesId'] = user_row['usuariosClientesId']
        session['Nombres'] = user_row['Nombres']
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""UPDATE estado_conexion
SET estado = CASE
               WHEN usuariosClientesId = '%s' THEN 1
               ELSE 0
            END;""", (session['usuariosClientesId'],))
        db.commit()
        cursor.close()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Las credenciales ingresadas no son válidas.'}), print("Error chele")


@app.route('/obtener_contenido_carrito')
def obtener_contenido_carrito():
    print("Dentro de obtener_contenido_carrito")
    contenido = render_template('contenido_carrito.html')
    print(contenido)
    return contenido


@app.route('/set_sucursal', methods=['POST'])
def set_sucursal():
    sucursalId = request.form.get('sucursalId')
    if sucursalId:
        session['sucursalId'] = sucursalId
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Sucursal no válida.'})


# Route for the user registration page
@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Información primer form

        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        cedula = request.form['cedula']
        correo = request.form['email']
        telefono = request.form['telefono']
        contrasena = request.form['password']

        # Información segundo form
        # Información modal

        car_year = request.form['car_year']
        car_make = request.form['car_make']
        car_model = request.form['car_model']
        car_cc = request.form['car_cc']
        car_img = request.form['car_img']

        # Información que sigue del form
        numeroPlaca = request.form['numeroPlaca']
        numeroChasis = request.form['numeroChasis']
        numeroMotor = request.form['numeroMotor']

        # Encripatando la contrasena
        password_hash = generate_password_hash(contrasena)

        # Insert user data into the database
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO usuarios_clientes (Nombres, Apellidos, Correo, Cedula, Telefono, Contraseña) VALUES (%s, %s, %s, %s, %s, %s)",
            (nombres, apellidos, correo, cedula, telefono, password_hash))

        usuariosClientesId = cursor.lastrowid

        # Insertar datos del vehículo en la tabla vehiculos
        cursor.execute(
            "INSERT INTO vehiculos (usuariosClientesId, cc, marca, modelo, año, imgUrl, placa, chasis, numeroMotor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (usuariosClientesId, car_cc, car_make, car_model, car_year, car_img, numeroPlaca, numeroChasis, numeroMotor))

        # Insertar datos en la tabla estado_conexion
        estado_conexion = 0  # Puedes establecer el estado según tu lógica de negocio
        estado_whatsapp = 0
        cursor.execute(
            "INSERT INTO estado_conexion (usuariosClientesId, estado, estado_whatsapp) VALUES (%s, %s, %s)",
            (usuariosClientesId, estado_conexion, estado_whatsapp))

        db.commit()
        cursor.close()

        print("SIMON CHELE TE REGISTRASTE CON TODO Y CARRO")

        return redirect(url_for('home'))

    # If accessing the registration page for the first time or GET request, show the registration form
    return render_template('/auth/register_user.html')


@app.errorhandler(404)
def not_found(error):
    return render_template('/error404.html')


@app.route('/lostpass', methods=['GET', 'POST'])
def lostpass():

    if request.method == 'POST':
        return render_template('/auth/lostpass.html', load=1)

    return render_template('/auth/lostpass.html')


@app.route('/tienda', methods=['GET', 'POST'])
def tienda():
    if request.method == 'GET':

        # Declaramos como false el titulo_check para que no se muestre el h3 titulo de la busqueda
        titulo_check = False

    # Declaramos como none para que no marque error en el contexto de pasar la variable titulo_busqueda
        titulo_busqueda = None
    # Obtener el término de búsqueda de la URL
        search_term = request.args.get('q', '')
        print(search_term)

        # Obtener el número de página actual
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * 9  # Calcular el offset para la paginación

        # Obtener el id_categoria de la URL
        id_categoria = request.args.get('id_categoria')

        db = connectionBD()
        cursor = db.cursor(dictionary=True)

        if id_categoria:  # Si se proporciona un id_categoria
            cursor.execute("""
        SELECT 
            p.id_producto, 
            p.nombre AS nombre_producto, 
            p.descripcion, 
            p.precio, 
            u.nombre AS unidad_medida, 
            c.nombre AS categoria, 
            i.ruta_archivo, 
            i.producto_id
        FROM productos p
        JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
        JOIN categorias c ON p.categoria_id = c.id_categoria
        LEFT JOIN imagenes i ON p.id_producto = i.producto_id
        JOIN inventario inv ON p.id_producto = inv.id_producto
        WHERE p.categoria_id = %s AND inv.sucursalId = %s
        ORDER BY p.nombre ASC
        LIMIT 9 OFFSET %s
        """, (id_categoria, session['sucursalId'], offset))

            productos = cursor.fetchall()

            cursor.execute("""
        SELECT COUNT(*) 
        FROM productos p
        JOIN inventario inv ON p.id_producto = inv.id_producto
        WHERE p.categoria_id = %s AND inv.sucursalId = %s
        """, (id_categoria, session['sucursalId']))

            total_productos = cursor.fetchone()['COUNT(*)']

            cursor.execute(
                'SELECT nombre FROM categorias WHERE id_categoria = %s', (id_categoria,))
            titulo_busqueda = cursor.fetchone()['nombre']
            titulo_check = True

        # Si se proporciona un término de búsqueda, realizar la búsqueda en la base de datos
        elif search_term:
            titulo_check = True
            cursor.execute("""
    SELECT 
        p.id_producto, 
        p.nombre AS nombre_producto, 
        p.descripcion, 
        p.precio, 
        u.nombre AS unidad_medida, 
        c.nombre AS categoria, 
        i.ruta_archivo, 
        i.producto_id
    FROM productos p
    JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
    JOIN categorias c ON p.categoria_id = c.id_categoria
    LEFT JOIN imagenes i ON p.id_producto = i.producto_id
    JOIN inventario inv ON p.id_producto = inv.id_producto
    WHERE (p.nombre LIKE %s OR c.nombre LIKE %s) AND inv.sucursalId = %s
    ORDER BY p.nombre ASC
    LIMIT 9 OFFSET %s
""", ('%' + search_term + '%', '%' + search_term + '%', session['sucursalId'], offset))

            print("Entró")
            productos = cursor.fetchall()

            cursor.execute("""
    SELECT COUNT(*) 
    FROM productos p
    JOIN inventario inv ON p.id_producto = inv.id_producto
    WHERE (p.nombre LIKE %s OR p.categoria_id IN (SELECT id_categoria FROM categorias WHERE nombre LIKE %s)) AND inv.sucursalId = %s
""", ('%' + search_term + '%', '%' + search_term + '%', session['sucursalId']))

            titulo_busqueda = search_term

            total_productos = cursor.fetchone()['COUNT(*)']

        else:
            # Consulta de productos sin término de búsqueda
            # Consulta de productos con paginación (ajustado a 9 productos por página)
            cursor.execute("""
    SELECT 
        p.id_producto, 
        p.nombre AS nombre_producto, 
        p.descripcion, 
        p.precio, 
        u.nombre AS unidad_medida, 
        c.nombre AS categoria, 
        i.ruta_archivo, 
        i.producto_id
    FROM productos p
    JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
    JOIN categorias c ON p.categoria_id = c.id_categoria
    LEFT JOIN imagenes i ON p.id_producto = i.producto_id
    JOIN inventario inv ON p.id_producto = inv.id_producto
    WHERE inv.sucursalId = %s
    ORDER BY p.nombre ASC
    LIMIT 9 OFFSET %s
""", (session['sucursalId'], offset))

            productos = cursor.fetchall()

            cursor.execute("""
    SELECT COUNT(*) 
    FROM productos p
    JOIN inventario inv ON p.id_producto = inv.id_producto
    WHERE inv.sucursalId = %s
""", (session['sucursalId'],))

            total_productos = cursor.fetchone()['COUNT(*)']

        # Consulta para contar el número total de productos

        # Calcular el número total de páginas
        total_paginas = (total_productos + 8) // 9
        print(total_paginas)

        # Consulta de categorías
        cursor.execute(
            'SELECT id_categoria, nombre FROM categorias ORDER BY nombre ASC')
        categorias = cursor.fetchall()
        cursor.close()

    return render_template('/shop-grid.html', productos=productos, categorias=categorias, page=page, total_paginas=total_paginas, titulo_check=titulo_check, titulo_busqueda=titulo_busqueda)


@app.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():
    producto_id = request.form.get('producto_id')
    cantidad = request.form.get('cantidad', 1)

    # Aquí, consulta la base de datos para obtener detalles del producto
    detalles_producto = obtener_detalles_productos([producto_id])[0]

    # Inicializar el carrito en la sesión si aún no existe
    if 'carrito' not in session:
        session['carrito'] = {}

    # Si el producto ya está en el carrito, aumenta la cantidad. Si no, añádelo.
    if producto_id in session['carrito']:
        session['carrito'][producto_id]['cantidad'] += int(cantidad)
    else:
        session['carrito'][producto_id] = {
            'nombre': detalles_producto['nombre'],
            'precio': detalles_producto['precio'],
            # 'imagen': detalles_producto['ruta_archivo'],  # Asumo que 'ruta_archivo' está en la tabla 'productos', sino, se debe ajustar.
            'cantidad': int(cantidad)
        }

    return jsonify(success=True, message="Producto agregado al carrito")


@app.route('/eliminar_del_carrito', methods=['POST'])
def eliminar_del_carrito():
    producto_id = request.form.get('producto_id')
    if producto_id in session['carrito']:
        del session['carrito'][producto_id]
        return jsonify(success=True, message="Producto eliminado del carrito")
    else:
        return jsonify(success=False, message="Producto no encontrado en el carrito")


@app.route('/vaciar_carrito', methods=['POST'])
def vaciar_carrito():
    session['carrito'] = {}
    return jsonify(success=True, message="Carrito vaciado")


@app.route('/calificar', methods=['GET', 'POST'])
def calificar():
    return render_template('/home.html', entrar=True)


@app.route('/login_system', methods=['GET', 'POST'])
def login_system():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']

        if not user or not password:
            error = "Debes completar todos los campos para continuar."
            return render_template('/auth/login_system.html', error=error)

        # Verifica las creedenciales en la base de datos
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM usuarios_sistema WHERE usuario = %s', (user,))
        user_row = cursor.fetchone()

        if user_row and check_password_hash(user_row['contraseña'], password):
            # Si las credenciales son validas, el colaborador se loguea
            session['usersis_id'] = user_row['usersis_id']
            session['name'] = user_row['nombres']
            session['rol'] = user_row['id_rol']
            return redirect(url_for('home_system'))
        else:
            # Si las credenciales son invalidas, se envía un mensaje de error
            error = "Las credenciales ingresadas no son válidas. Por favor, inténtalo de nuevo."
            return render_template('/auth/login_system.html', error=error)
    if session.get("usersis_id"):
        return redirect(url_for('home_system'))
    # Si entrea a la ruta del login_colaborador este renderiza la plantilla
    return render_template('/auth/login_system.html')


@app.route('/home_system', methods=['GET', 'POST'])
@login_requiredUser_system
def home_system():
    return render_template('home_system.html')


@app.route('/asistencia_ia', methods=['GET', 'POST'])
@login_requiredUser_system
def asistencia_ia():

    if request.method == 'POST':
        #         # Establecer la clave de la API de ChatGPT (Se hace con el .env variable de entorno)
        # openai.api_key = os.getenv("OPENAI_API_KEY")

        # # Crear una variable para el prompt
        # prompt = "Eres un asistente para el negocio Lubicentro dos hermanos y crearás un reporte de la cantidad de productos: "
        # # Crear una variable para la consulta a la base de datos
        # query = """SELECT p.id_producto, p.nombre AS nombre_producto, p.descripcion, p.precio, u.nombre AS unidad_medida, c.nombre AS categoria
        # FROM productos p
        # JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
        # JOIN categorias c ON p.categoria_id = c.id_categoria
        # ORDER BY p.nombre ASC"""
        pregunta_prompt = request.form["pregunta_prompt"]

        # 1. Cargar la bbdd con langchain

        db = SQLDatabase.from_uri(
            "mysql://root:1233456@localhost:3306/proyectoIA")

        # 2. Importar las APIs

        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

        # 3. Crear el LLM

        toolkit = SQLDatabaseToolkit(db=db, llm=OpenAI(temperature=0))

        agent_executor = create_sql_agent(
            llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613"),
            toolkit=toolkit,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS
        )

        resultado = agent_executor.run(pregunta_prompt)

        return render_template("asistenciaIA.html", response=resultado)

        # llm = ChatOpenAI(temperature=0,model_name='gpt-3.5-turbo')

        # # 4. Crear la cadena
        # cadena = SQLDatabase(llm = llm, database = db, verbose=False)

        # # 5. Formato personalizado de respuesta
        # formato = """
        # Data una pregunta del usuario:
        # 1. crea una consulta de sqlite3
        # 2. revisa los resultados
        # 3. devuelve el dato
        # 4. si tienes que hacer alguna aclaración o devolver cualquier texto que sea siempre en español
        # #{question}
        # """

        # # 6. Función para hacer la consulta

        # def consulta(pregunta_prompt):
        #     consulta = formato.format(question = pregunta_prompt)
        #     resultado = cadena.run(consulta)
        #     print(resultado)

        # consulta(pregunta_prompt)

    return render_template('asistenciaIA.html', response="")


@app.route('/test', methods=['GET', 'POST'])
@cross_origin()
def test():

    # subscription_key = '9c66d63084ff47dc99cbbb10b4d5dd9d'

    # search_url = "https://api.bing.microsoft.com/v7.0/search"

    # def buscar_manual(query, num_links=5):
    #     headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    #     params = {"q": query, "fileType": "pdf", "count": num_links}
    #     response = requests.get(search_url, headers=headers, params=params)
    #     results = response.json()
    #     links = [result["url"] for result in results["webPages"]["value"]]
    #     print(f"Enlace para descargar el PDF: {links}")  # Imprime el enlace del PDF
    #     return links

    #     # Descarga el primer PDF que se encuentra en la lista de enlaces proporcionada por Bing
    # def descargar_primer_pdf(links, keywords):
    #     for link in links:
    #         response = requests.get(link)
    #         if response.status_code == 200:
    #             with open("manual.pdf", "wb") as pdf_file:
    #                 pdf_file.write(response.content)
    #             # Extraer oraciones del PDF descargado
    #             extracted_sentences = extraer_oraciones_con_palabras_clave("manual.pdf", keywords)
    #             # Verificar si las palabras clave están presentes en las oraciones
    #             if any(any(keyword in sentence.lower() for keyword in keywords) for sentence in extracted_sentences):
    #                 return extracted_sentences
    #     return []

    # # Abre el PDF y extrae oraciones con palabras clave, limitando a 2000 palabras
    # def extraer_oraciones_con_palabras_clave(pdf_file_path, keywords):
    #     extracted_sentences = []
    #     total_words = 0
    #     try:
    #         with fitz.open(pdf_file_path) as pdf_document:
    #             for page_num in range(pdf_document.page_count):
    #                 page = pdf_document[page_num]
    #                 text = page.get_text()
    #                 paragraphs = text.split('\n\n')  # Suponiendo que los párrafos están separados por dos saltos de línea
    #                 for paragraph in paragraphs:
    #                     if any(keyword in paragraph.lower() for keyword in keywords):
    #                         sentences = paragraph.split('.')  # Suponiendo que las oraciones están separadas por puntos
    #                         for sentence in sentences:
    #                             word_count = len(sentence.split())
    #                             if total_words + word_count <= 2000:
    #                                 extracted_sentences.append(sentence.strip())
    #                                 total_words += word_count
    #                             else:
    #                                 break
    #                     if total_words >= 2000:
    #                         break
    #                 if total_words >= 2000:
    #                     break
    #     except Exception as e:
    #         print(f"Error al leer el archivo PDF: {e}")
    #     return extracted_sentences

    # # Almacena las oraciones que cumplen con los criterios en una lista
    # def almacenar_oraciones(pdf_path, keywords):
    #     extracted_sentences = extraer_oraciones_con_palabras_clave(pdf_path, keywords)
    #     # Haz lo que necesites con las oraciones extraídas
    #     return extracted_sentences

    # if request.method == "GET":

    #     search_query = 'TOYOTA YARIS 2008 MANUAL filetype:PDF'
    #     links = buscar_manual(search_query)
    #     keywords = ["oil", "tire", "oil filters", "oil quality"]  # Palabras clave a buscar en el PDF
    #     extracted_sentences = descargar_primer_pdf(links, keywords)

    #     if extracted_sentences:
    #         print(extracted_sentences)
    #     else:
    #         print("No se encontraron enlaces con palabras clave en el PDF.")

    # # Tu clave de suscripción de la API de Bing
    # subscription_key = '9c66d63084ff47dc99cbbb10b4d5dd9d'
    # search_url = "https://api.bing.microsoft.com/v7.0/search"

    # # Palabras clave que estás buscando
    # palabras_clave = ["Recommend Oil change", "Oil filters", "Lubricants and oils", "Service recommendations", "Vehicle inspection", "Maintenance program", "Vehicle fluids", "Recommended oil brands", "Oil change intervals", "Types of oils", "Common mechanical problems", "Vehicle issue solutions", "Oil quality", "Industry standards"]

    # # Término de búsqueda general
    # search_term = "Honda Fit 2007"

    # # Función para buscar sitios web y extraer 2 párrafos con palabras clave
    # def buscar_y_extraer_parrafos():
    #     headers = {"Ocp-Apim-Subscription-Key": subscription_key}

    #     for keyword in palabras_clave:
    #         query = f'{search_term} + "{keyword}"'
    #         params = {"q": query, "textDecorations": True, "textFormat": "HTML"}

    #         response = requests.get(search_url, headers=headers, params=params)
    #         response.raise_for_status()
    #         search_results = response.json()

    #         for result in search_results["webPages"]["value"]:
    #             url = result["url"]
    #             print(f"Buscando en: {url}")

    #             # Obtener contenido de la página web
    #             response = requests.get(url)
    #             soup = BeautifulSoup(response.content, "html.parser")

    #             # Contador para contar los párrafos encontrados
    #             paragraphs_found = 0

    #             # Buscar párrafos con la palabra clave y extraer dos
    #             for p in soup.find_all("p"):
    #                 if keyword.lower() in p.text.lower():
    #                     print(f"Palabra clave encontrada: {keyword}")
    #                     print(f"Párrafo: {p.text}")
    #                     print("------")
    #                     paragraphs_found += 1

    #                     # Almacenar los dos párrafos encontrados y luego salir del bucle
    #                     if paragraphs_found == 2:
    #                         break

    #             # Si encontramos los dos párrafos, salir del bucle de resultados
    #             if paragraphs_found == 2:
    #                 break

    # # Llamada a la función
    # buscar_y_extraer_parrafos()

    # subscription_key = '9c66d63084ff47dc99cbbb10b4d5dd9d'

    # search_url = "https://api.bing.microsoft.com/v7.0/search"
    # Clave de la API de Bing

    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
SELECT v.marca, v.modelo, v.año, v.imgUrl
FROM vehiculos v
JOIN estado_conexion ec ON v.usuariosClientesId = ec.usuariosClientesId
WHERE ec.estado = 1;
        """)

    car_row = cursor.fetchone()

    db.close()

    if car_row:
        # Almacena los valores en variables
        marca = car_row['marca']
        modelo = car_row['modelo']
        año = car_row['año']
        imgUrl = car_row['imgUrl']
        
        # Ahora puedes usar estas variables según tus necesidades
        print("Marca:", marca)
        print("Modelo:", modelo)
        print("Año:", año)
        print("URL de la imagen:", imgUrl)
    else:
        print("No se encontraron vehículos con estado 1.")

    API_KEY = '9c66d63084ff47dc99cbbb10b4d5dd9d'

    SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
    # Lista de palabras clave
    PALABRAS_CLAVE = ['Oil RECOMMENDATION', 'OIL FILTER RECOMMENDATION',
                      'TIRES SIZE', 'COMMON ISSUES', 'OIL CHANGE']
    # Modelo de automóvil constante
    MODELO_AUTO = f'{marca} {modelo}, {año}'

    resultados = {}
    for keyword in PALABRAS_CLAVE:
        query = f"{MODELO_AUTO} {keyword}"
        headers = {'Ocp-Apim-Subscription-Key': API_KEY}
        params = {
            'q': query,
            'count': 5
        }
        response = requests.get(
            SEARCH_ENDPOINT, headers=headers, params=params)
        results = response.json()

        # Guardar los snippets en el diccionario de resultados
        snippets = []
        if 'webPages' in results.keys() and 'value' in results['webPages']:
            for resultado in results['webPages']['value']:
                snippet = resultado.get(
                    'snippet', 'No hay descripción disponible')
                snippets.append(snippet)
        resultados[keyword] = snippets

    car_model = {
            'carro' : MODELO_AUTO,
            'imgUrl' : imgUrl
        }
        # Agregar car_model como una nueva clave en resultados
    resultados['CAR_DETAILS'] = car_model
    
    return jsonify(resultados)

    return render_template('test.html')


@app.route('/get_years', methods=['GET'])
def get_years():
    api_url = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=all-vehicles-model&rows=0&facet=year"
    response = requests.get(api_url)
    years = set()
    if response.status_code == 200:
        data = response.json()
        for facet in data['facet_groups']:
            if facet['name'] == 'year':
                for item in facet['facets']:
                    years.add(item['name'])
    return jsonify(sorted(list(years), reverse=True))


@app.route('/get_makes', methods=['GET'])
def get_makes():
    year = request.args.get('year')
    api_url = f"https://public.opendatasoft.com/api/records/1.0/search/?dataset=all-vehicles-model&rows=100&facet=year&refine.year={year}"
    response = requests.get(api_url)
    makes = set()
    if response.status_code == 200:
        data = response.json()
        for record in data['records']:
            makes.add(record['fields']['make'])
    return jsonify(sorted(list(makes)))


@app.route('/get_models', methods=['GET'])
def get_models():
    year = request.args.get('year')
    make = request.args.get('make')
    api_url = f"https://public.opendatasoft.com/api/records/1.0/search/?dataset=all-vehicles-model&rows=100&facet=year&refine.year={year}&facet=make&refine.make={make}"
    response = requests.get(api_url)
    models = set()
    if response.status_code == 200:
        data = response.json()
        for record in data['records']:
            models.add(record['fields']['model'])
    return jsonify(sorted(list(models)))


@app.route('/get_engine_displacements', methods=['GET'])
def get_engine_displacements():
    year = request.args.get('year')
    make = request.args.get('make')
    model = request.args.get('model')
    api_url = f"https://public.opendatasoft.com/api/records/1.0/search/?dataset=all-vehicles-model&rows=100&facet=year&refine.year={year}&facet=make&refine.make={make}&facet=model&refine.model={model}"
    response = requests.get(api_url)
    engine_displacements = set()
    if response.status_code == 200:
        data = response.json()
        for record in data['records']:
            engine_displacements.add(record['fields'].get('displ', 'N/A'))
    return jsonify(list(engine_displacements))

# Función para obtener todos los productos


def obtener_productos():
    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * from PRODUCTOS")
    productos = cursor.fetchall()
    cursor.close()

    return productos

# RUTA API PARA VOICEFLOW TODOS LOS PRODUCTOS


@app.route('/api/productos', methods=['GET'])
@cross_origin()  # Esto habilita CORS solo para esta ruta
def api_productos():
    productos = obtener_productos()
    respuesta = {"productos": productos}
    return jsonify(respuesta)


@app.route('/get_nombre_apellido', methods=['GET'])
@cross_origin()
def get_nombre_apellido():
    db = connectionBD()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT uc.usuariosClientesId, uc.nombres, uc.apellidos, uc.correo
            FROM usuarios_clientes uc
            JOIN estado_conexion ec ON uc.usuariosClientesId = ec.usuariosClientesId
            WHERE estado = 1
            ORDER BY ec.fecha_cambio_estado DESC
            LIMIT 1;
        """)

        user_row = cursor.fetchone()

        if user_row and user_row['nombres'] and user_row['apellidos']:
            primer_nombre = user_row['nombres']
            primer_apellido = user_row['apellidos']

            response = {
                'primer_nombre': primer_nombre,
                'primer_apellido': primer_apellido
            }
            return jsonify(response)
        else:
            return jsonify(error='No se encontraron usuarios conectados'), 404

    except Exception as e:
        return jsonify(error=str(e)), 500

    finally:
        cursor.close()


@app.route('/search_images', methods=['GET'])
def search_images():
    year = request.args.get('year')
    make = request.args.get('make')
    model = request.args.get('model')

    query = f"{year} {make} {model} car"

    subscription_key = "9c66d63084ff47dc99cbbb10b4d5dd9d"
    endpoint = "https://api.bing.microsoft.com/v7.0/images/search"

    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    # Transparent para buscar imágenes PNG
    params = {"q": query, "count": 3, "imageType": "Transparent"}

    response = requests.get(endpoint, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        img_urls = [img['thumbnailUrl'] for img in data['value']]
        return jsonify(img_urls)

    return jsonify(error="No se pudo obtener las imágenes"), 500


# Suponiendo una lista de usuarios en lugar de una base de datos real
usuarios = [
    {'nombre': 'Bumbul', 'numero_telefono': '50585051703'},
    {'nombre': 'Jhona', 'numero_telefono': '50581719517'},
    {'nombre': 'Denisse', 'numero_telefono': '50581401626'},
    {'nombre': 'Kairo', 'numero_telefono': '50577784430'}
    # ... más usuarios
]


# def enviar_notificacion():

#     for usuario in usuarios:
#         numero_telefono = usuario['numero_telefono']
#         # Mensaje personalizado
#         mensaje_personalizado = f'''*Hola {usuario["nombre"]} WA WA WA*, este es un mensaje de OilWise, el servicio inteligente de cambio de aceite. 🚗\n
# Hemos analizado el uso de tu vehículo y te recomendamos que realices un cambio de aceite pronto para mantenerlo en óptimas condiciones. ⚙️\n
# Puedes programar tu cita con nosotros en este enlace: https://oilwise.com/cita\n
# Además, nos gustaría saber tu opinión sobre nuestro servicio. ¿Te ha sido útil? ¿Qué podemos mejorar? Déjanos tu feedback en este otro enlace: https://oilwise.com/feedback\n
# Gracias por confiar en OilWise, el servicio inteligente de cambio de aceite. 😊'''
#         url = f'http://api.textmebot.com/send.php?recipient={numero_telefono}&apikey={API_KEY}&text={mensaje_personalizado}'
#         response = requests.get(url)
#         if response.status_code == 200:
#             print(f'Mensaje enviado a {usuario["nombre"]}')
#         else:
#             print(f'Error al enviar el mensaje a {usuario["nombre"]}')
#         # Esperar 5 segundos antes de enviar el siguiente mensaje
#         time.sleep(10)

def enviar_notificacion():

    url = "https://graph.facebook.com/v17.0/103770299497358/messages"
    headers = {
        "Authorization": "EAAJRjmjgun8BO3ZC7m4kZB1MUHR2CdMlvfZChpnllsPaNTXf0jSmgY7bZBP2oRIruQZBhFMdBs3VhsnjDS7l6B5e5kepaw3zdi0K02T8CcLreRgFGIoKmEiIkkNm6pkO1hvOZBRS7XXLCizCWW2baZBy0exkS8kU712ZB8CaHuM4Llb0qpGN1Qj05ZCaqmSAZBMMKBDrFgZAo1yZA11y8CteVlW4x8vAVZBZClGa0yZAWK7XSIW7fQZD",
        "Content-Type": "application/json"
    }

    for usuario in usuarios:

        nombre = usuario['nombre']
        numero_telefono = usuario['numero_telefono']

        print(f"{nombre} {numero_telefono}")

        data = {
            "messaging_product": "whatsapp",
            "to": f"{numero_telefono}",
            "type": "template",
            "template": {
                "name": "recordatorio_aceite",
                "language": {
                    "code": "es_MX"
                },
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "text",
                                "text": f"{nombre}"
                            }
                        ]
                    }
                ]
            }
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print("Status Code:", response.status_code)
        print("Response:")
        print(response.text)


scheduler = BackgroundScheduler()
# Ajusta la hora a la que deseas enviar la notificación
trigger = CronTrigger(hour=10, minute=25)
scheduler.add_job(enviar_notificacion, trigger=trigger)
scheduler.start()


# Logout
@app.route('/Cerrar_Sesion')
def Cerrar_Sesion():
    # Cambiar el estado de la sesion a desconectado de cuenta osea 0
    db = connectionBD()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""UPDATE estado_conexion
SET estado = 0
WHERE usuariosClientesId = '%s'""", (session['usuariosClientesId'],))
    db.commit()
    cursor.close()
    session.pop('usuariosClientesId', None)
    session.pop('Nombres', None)
    print("Sesión cerrada exitosamente")
    return redirect(url_for('home'))


@app.route('/Cerrar_Sesion_Sistema')
def Cerrar_Sesion_Sistema():
    # Clear session variables
    session.pop('usersis_id', None)
    session.pop('Nombres', None)
    session.pop('name', None)
    session.pop('rol', None)

    return redirect(url_for('login_system'))


# Print
# Ejecuta la aplicación Flask
if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)  # Habilitar registros de nivel DEBUG
    app.run(host='0.0.0.0')
    app.run()
