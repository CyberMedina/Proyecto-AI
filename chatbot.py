import os
import re
import openai
from openai import OpenAI
from flask import request, jsonify
from datetime import datetime
from fuzzywuzzy import process, fuzz
from models.prompts import Prompt_chatbot

# Inicializar cliente OpenAI moderno
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Historial del chat
chat_history = [
    {
        "role": "system",
        "content": Prompt_chatbot,
    }
]

# Límite diario de mensajes
message_count = 0
MAX_MESSAGES = 12
last_interaction_date = datetime.now().date()

# Función para consultar centros de acopio
def get_nearest_recycling_centers():
    return "Estos son los centros de acopio chele"

# Preguntas predefinidas
predefined_questions = {
    'horarios': [
        'cuales son sus horarios',
        'a que hora trabajan',
        'cual es el horario de atencion',
        'cuando estan abiertos',
        'a que hora abren',
        'horario de trabajo',
        'horarios',
        'cuando trabajan',
    ],
    'centros_acopio': [
        'donde estan los centros de acopio',
        'centros de acopio cercanos',
        'donde puedo llevar reciclaje',
        'lugares para reciclar',
        'puntos de acopio',
    ],
    'contacto': [
        'como contactar',
        'numero de contacto',
        'cual es su numero de telefono',
        'contacto',
        'telefono',
    ]
}

# Función para detectar preguntas frecuentes
def handle_predefined_questions(user_message):
    for key, phrases in predefined_questions.items():
        for phrase in phrases:
            score = fuzz.token_sort_ratio(user_message.lower(), phrase)
            if score >= 70:
                if key == 'horarios':
                    return 'Nuestro horario es de 8 AM a 6 PM, de lunes a sábado.'
                elif key == 'centros_acopio':
                    return get_nearest_recycling_centers()
                elif key == 'contacto':
                    return 'Puedes contactarnos al número: (505) 1234-5678.'
    return None

# Función principal del chatbot
def chatbot_message(user_message):
    global message_count, last_interaction_date

    try:
        current_date = datetime.now().date()
        if current_date != last_interaction_date:
            message_count = 0
            last_interaction_date = current_date

        if message_count >= MAX_MESSAGES:
            return jsonify({'error': 'Has alcanzado el límite de 12 mensajes por hoy.'}), 403

        predefined_response = handle_predefined_questions(user_message)
        if predefined_response:
            message_count += 1
            return jsonify({
                'reply': predefined_response,
                'current_count': message_count,
                'total_messages': MAX_MESSAGES
            })

        chat_history.append({
            "role": "user",
            "content": user_message
        })

        # ✅ Versión actual del SDK usa client.chat.completions.create
        chat_completion = client.chat.completions.create(
            model="gpt-4o",  # o "gpt-4o-mini" si está disponible
            messages=chat_history
        )

        bot_reply = chat_completion.choices[0].message.content.strip()

        chat_history.append({
            "role": "assistant",
            "content": bot_reply
        })

        message_count += 1

        return jsonify({
            'reply': bot_reply,
            'current_count': message_count,
            'total_messages': MAX_MESSAGES
        })

    except Exception as e:
        print(e)
        return 'Error en la comunicación con el servidor. Por favor, intenta de nuevo más tarde.', 500
