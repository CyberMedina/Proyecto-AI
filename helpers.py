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