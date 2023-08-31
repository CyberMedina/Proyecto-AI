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
from helpers import in_session

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config.from_mapping(config)




app.jinja_env.globals['g'] = g #Se instancia la variable global para ser usada en jinja


#No puuede ser cambiada esta función, ya que esta función es una palabra reservada
@app.before_request
def before_request():
    if 'user_id' in session:
        db = connectionBD()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT nombres, apellidos FROM usuarios WHERE user_id = %s', (session['user_id'],))
        user_row = cursor.fetchone()
        cursor.close()

        g.user_id = session['user_id']
        g.nombres = user_row['nombres']
        g.apellidos = user_row['apellidos']

        
    
    if 'user_id' in session:
        g.user_id = session['user_id']
        print(g.user_id)

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
    return render_template('/home.html')

# Ruta para el inicio de sesión y además abriendo por modal
@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    return render_template('home.html', error3=True)

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

@app.route('/calificar', methods=['GET', 'POST'])
def calificar():
    return render_template('/home.html', entrar=True)    


# Logout
@app.route('/Cerrar_Sesion')
def logout():
    # Clear session variables
    session.pop('user_id', None)
    session.pop('name', None)
    print("Sesión cerrada exitosamente")
    return redirect(url_for('home'))


# Ejecuta la aplicación Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0')
    app.run()


