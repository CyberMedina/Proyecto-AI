import os
from flask import Flask
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

# Función para establecer conexión en la base de datos
# Local
# def connectionBD():
#     db = mysql.connector.connect(
#         host="127.0.0.1",
#         user="root",
#         password="1233456",
#         database="proyectoia"
#     )
#     return db

def connectionBD():
    try:
        db = mysql.connector.connect(
            host= os.getenv("DB_HOSTNAME"),
            user= os.getenv("DB_USERNAME"),
            password= os.getenv("DB_PASSWORD"),
            database= os.getenv("DB_DATABASENAME"),
            port=3306
        )
        if db.is_connected():
            return db  # Retorna la conexión si fue exitosa
        else:
            print("Conexión fallida")
            return None  # Retorna None si la conexión falla
    except Error as e:
        print("Error:", e)
        return None  # Retorna None si hay un error


