from flask import Flask
from flask_mysqldb import MySQL, MySQLdb
import mysql.connector

# Función para establecer conexión en la base de datos
def connectionBD():
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="1233456",
        database="proyectoia"
    )
    return db

config = {
    "DEBUG": True  # Comando para correr la aplicación en DEBUG
}




