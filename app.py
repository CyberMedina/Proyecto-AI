import hashlib
import re
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from flask_mysqldb import MySQL, MySQLdb
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, g # Para poder realizar variables globales en jinja2
from urllib.parse import urlencode #Dependencia utilizada para redirigir hacia modals
from config import connectionBD, config
from helpers import in_session, login_requiredUser_system
import os
import openai
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config.from_mapping(config)



# Establecer la clave de la API de ChatGPT
openai.api_key = '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'

# Crear una variable para el prompt
prompt = "Eres un asistente para el negocio Lubicentro dos hermanos y crearás un reporte de la cantidad de productos: "
# Crear una variable para la consulta a la base de datos
query = """SELECT p.id_producto, p.nombre AS nombre_producto, p.descripcion, p.precio, u.nombre AS unidad_medida, c.nombre AS categoria
FROM productos p
JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
JOIN categorias c ON p.categoria_id = c.id_categoria
ORDER BY p.nombre ASC"""




app.jinja_env.globals['g'] = g #Se instancia la variable global para ser usada en jinja


#No puuede ser cambiada esta función, ya que esta función es una palabra reservada
@app.before_request
def before_request():
    if 'usuariosClientesId' in session:
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT Nombres, Apellidos FROM usuarios_clientes WHERE usuariosClientesId = %s', (session['usuariosClientesId'],))
        user_row = cursor.fetchone()
        cursor.close()

        g.user_id = session['usuariosClientesId']
        g.nombres = user_row['Nombres']
        g.apellidos = user_row['Apellidos']

    if 'usersis_id' in session:
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT us.usersis_id, us.nombres, us.apellidos, us.correo, r.rolname FROM usuarios_sistema us JOIN rol r ON us.id_rol = r.id_rol WHERE us.usersis_id = %s', (session['usersis_id'],))
        user_row = cursor.fetchone()
        cursor.close()

        g.id_rol = session['usersis_id']
        g.nombres = user_row['nombres']
        g.apellidos = user_row['apellidos']
        g.correo = user_row['correo']
        g.rolname = user_row['rolname']




    
    

@app.after_request
def after_request(response):
    """Asegura que las respuestas del servidor no se almacenen en caché del navegador"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#Actualiza el proyecto al realizar modificaciones en el HTML en la carpeta templates
app.config["TEMPLATES_AUTO_RELOAD"] = True



#Esta es una forma de almacenar la información del usuario en el servidor para luego ser utilizada en la aplicación
app.config["SESSION_PERMANENT"] = False #Configura la sesion para que no sea permanente y se cierre cuando se cierre el navegador
app.config["SESSION_TYPE"] = "filesystem" # Define el tipo de almacenamiento para las sesiones, utilizando el almacenamiento en el sistema de archivos del servidor
Session(app)



# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():
    
    if request.method == 'GET':
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT id_categoria, nombre FROM categorias ORDER BY nombre ASC')
        categorias = cursor.fetchall()
        cursor.close()



    return render_template('/index.html', categorias=categorias)







# Route for the user registration page
@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Get form data
        tipo_user = 2
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        password = request.form['password']
        repite_password = request.form['repite_password']
        sexo = request.form['sexo']

        # Check if user already exists in the database
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM login_python WHERE email = %s', (email,))
        account = cursor.fetchone()
        cursor.close()
        if account:
            error = "La cuenta de correo electrónico ya existe."
            return render_template('/auth/register.html', error=error)

        # Check if passwords match
        if password != repite_password:
            error = "Las contraseñas no coinciden. Por favor, inténtalo de nuevo."
            return render_template('/auth/register.html', error=error)

        # Hash the password using SHA256
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Insert user data into the database
        cursor = db.cursor()
        cursor.execute("INSERT INTO login_python (tipo_user, nombre, apellido, email, password, sexo) VALUES (%s, %s, %s, %s, %s, %s)", (tipo_user, nombre, apellido, email, password_hash, sexo))
        db.commit()
        cursor.close()
        

        msg = "Registro exitoso!"
        return render_template('/auth/login.html', msg=msg)
    
    # Get the list of countries from the database
    # db = connectionBD()
    # cursor = db.cursor(dictionary=True)
    # cursor.execute('SELECT nombre FROM departamentos')
    # countries = cursor.fetchall()
    # cursor.close()

    # Pass the list of countries to the template
    return render_template('/auth/register_user.html')

    # If accessing the registration page for the first time or GET request, show the registration form
    return render_template('/auth/register.html')

# El tipico error 404 cuando la página no existe
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
        # Obtener el término de búsqueda de la URL
        search_term = request.args.get('q', '')
        print(search_term)


        page = request.args.get('page', 1, type=int)  # Obtener el número de página actual
        offset = (page - 1) * 9  # Calcular el offset para la paginación

        id_categoria = request.args.get('id_categoria')  # Obtener el id_categoria de la URL

        db = connectionBD()
        cursor = db.cursor(dictionary=True)

        if id_categoria:  # Si se proporciona un id_categoria
            cursor.execute("""
            SELECT p.id_producto, p.nombre AS nombre_producto, p.descripcion, p.precio, u.nombre AS unidad_medida, c.nombre AS categoria, i.ruta_archivo, i.producto_id
            FROM productos p
            JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
            JOIN categorias c ON p.categoria_id = c.id_categoria
            JOIN imagenes i ON p.id_producto = i.producto_id
            WHERE p.categoria_id = %s
            ORDER BY p.nombre ASC
            LIMIT 9 OFFSET %s
            """, (id_categoria, offset))

            productos = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) FROM productos WHERE categoria_id = %s", (id_categoria,))
            total_productos = cursor.fetchone()['COUNT(*)']


        # Si se proporciona un término de búsqueda, realizar la búsqueda en la base de datos
        elif search_term:
            cursor.execute("""
            SELECT p.id_producto, p.nombre AS nombre_producto, p.descripcion, p.precio, u.nombre AS unidad_medida, c.nombre AS categoria, i.ruta_archivo, i.producto_id
            FROM productos p
            JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
            JOIN categorias c ON p.categoria_id = c.id_categoria
            LEFT JOIN imagenes i ON p.id_producto = i.producto_id
            WHERE p.nombre LIKE %s OR c.nombre LIKE %s
            ORDER BY p.nombre ASC
            LIMIT 9 OFFSET %s
            """, ('%' + search_term + '%', '%' + search_term + '%', offset))

            print("Entró")
            productos = cursor.fetchall()


            # Consulta para contar el número total de productos con la búsqueda
            cursor.execute("""
            SELECT COUNT(*) 
            FROM productos 
            WHERE nombre LIKE %s OR categoria_id IN (SELECT id_categoria FROM categorias WHERE nombre LIKE %s)
            """, ('%' + search_term + '%', '%' + search_term + '%'))

            total_productos = cursor.fetchone()['COUNT(*)']
            
        else:
            # Consulta de productos sin término de búsqueda
            # Consulta de productos con paginación (ajustado a 9 productos por página)
            cursor.execute("""
            SELECT p.id_producto, p.nombre AS nombre_producto, p.descripcion, p.precio, u.nombre AS unidad_medida, c.nombre AS categoria, i.ruta_archivo, i.producto_id
            FROM productos p
            JOIN unidades_medida u ON p.unidad_medida_id = u.id_unidad
            JOIN categorias c ON p.categoria_id = c.id_categoria
            LEFT JOIN imagenes i ON p.id_producto = i.producto_id
            ORDER BY p.nombre ASC
            LIMIT 9 OFFSET %s
            """, (offset,))
            productos = cursor.fetchall()

            
            cursor.execute("SELECT COUNT(*) FROM productos")
            total_productos = cursor.fetchone()['COUNT(*)']





        # Consulta para contar el número total de productos


        


        

        # Calcular el número total de páginas
        total_paginas = (total_productos + 8) // 9
        print(total_paginas)

        # Consulta de categorías
        cursor.execute('SELECT id_categoria, nombre FROM categorias ORDER BY nombre ASC')
        categorias = cursor.fetchall()
        cursor.close()

    return render_template('/shop-grid.html', productos=productos, categorias=categorias, page=page, total_paginas=total_paginas)


# Ruta para el inicio de sesión y además abriendo por modal
@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            error = "Debes completar todos los campos para continuar."
            return redirect(url_for('home', error=error))

        # Verifica las credenciales en la base de datos
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM usuarios_clientes WHERE correo = %s', (email,))
        user_row = cursor.fetchone()

        if user_row and check_password_hash(user_row['Contraseña'], password):
            # Si las credenciales son validas, el cliente se loguea
            session['usuariosClientesId'] = user_row['usuariosClientesId']
            session['Nombres'] = user_row['Nombres']
            print("Inicio de sesión exitoso")
            return redirect(url_for('home'))
        else:
            # Si las credenciales son invalidas, se envía un mensaje de error
            error = "Las credenciales ingresadas no son válidas. Por favor, inténtalo de nuevo."
            print("Ocurrió un error chele")
            return render_template('index.html', error=error)
            cursor.close()
    return render_template('index.html', error3=True)

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
        cursor.execute('SELECT * FROM usuarios_sistema WHERE usuario = %s', (user,))
        user_row = cursor.fetchone()
        cursor.close()

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
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        # Suponiendo que 'results' es una lista de resultados




        # Crear un cursor para ejecutar consultas


        # Ejecutar la consulta y obtener los resultados
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            for key, value in row.items():
                if isinstance(value, Decimal):
                    row[key] = float(value)

        # Cerrar el cursor y la conexión
        cursor.close()

        # Imprimir los resultados de la consulta
        

        # Convertir cada elemento de results a cadena si es necesario
        results_str = [str(result) for result in results]

        content = prompt + ' '.join(results_str)

        print(content)

        # Crear una variable para el chat con ChatGPT
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
        {
        "role": 'user',
        "content": content
        }
    ],
        temperature=0.8,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )

        # Imprimir la respuesta de ChatGPT
        print(response['choices'][0]['message']['content'])
        return render_template('asistenciaIA.html', response=response['choices'][0]['message']['content']) 



    return render_template('asistenciaIA.html', response="")   
# Logout
@app.route('/Cerrar_Sesion')
def Cerrar_Sesion():
    # Clear session variables
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


# Ejecuta la aplicación Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0')
    app.run()


