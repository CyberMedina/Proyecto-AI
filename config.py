from flask import Flask
from flask_mysqldb import MySQL, MySQLdb
import mysql.connector

# Función para establecer conexión en la base de datos
def connectionBD():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1233456",
        database="Velaroma"
    )
    return db

config = {
    "DEBUG": True  # Comando para correr la aplicación en DEBUG
}




