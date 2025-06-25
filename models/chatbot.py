import re
from flask import request, jsonify
from datetime import datetime
from fuzzywuzzy import process, fuzz

from openaiClient import client

from models.prompts import Prompt_chatbot




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

# Función para consultar centros de acopio desde la base de datos
def get_nearest_recycling_centers():

    return "Estos son los centros de acopio chele"


# Lista de preguntas predefinidas y sus acciones
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



# Función para manejar preguntas usando fuzzy matching
def handle_predefined_questions(user_message):
    for key, phrases in predefined_questions.items():
        # Buscar si alguna de las frases coincide con el mensaje
        for phrase in phrases:
            score = fuzz.token_sort_ratio(user_message.lower(), phrase)
            if score >= 70:
                # Define la respuesta basada en la clave (horarios, centros de acopio, etc.)
                if key == 'horarios':
                    return 'Nuestro horario es de 8 AM a 6 PM, de lunes a sábado.'
                elif key == 'centros_acopio':
                    return get_nearest_recycling_centers()
                elif key == 'contacto':
                    return 'Puedes contactarnos al número: (505) 1234-5678.'
    return None


def chatbot_message(user_message):
    global message_count, last_interaction_date

    try:
        # Verificar si ha pasado un día y restablecer el contador
        current_date = datetime.now().date()
        if current_date != last_interaction_date:
            message_count = 0
            last_interaction_date = current_date

        # Verificar si el usuario alcanzó el límite de mensajes
        if message_count >= MAX_MESSAGES:
            return jsonify({'error': 'Has alcanzado el límite de 12 mensajes por hoy.'}), 403

        # Revisar si el mensaje tiene una pregunta predefinida
        predefined_response = handle_predefined_questions(user_message)

        if predefined_response:
            # Incrementar el contador de mensajes
            message_count += 1

            # Si el mensaje coincide con una pregunta predefinida, devolver esa respuesta
            return jsonify({
                'reply': predefined_response,
                'current_count': message_count,
                'total_messages': MAX_MESSAGES
            })

        # Si no hay coincidencia, proceder con GPT
        chat_history.append({
            "role": "user",
            "content": user_message
        })

        # Llamada a la API de GPT solo si no hay coincidencias
        chat_completion = client.chat.completions.create(
            messages=chat_history,
            model="gpt-4o-mini",
        )
        
        # Obtener la respuesta de GPT y actualizar el historial
        bot_reply = chat_completion.choices[0].message.content.strip()

        chat_history.append({
            "role": "assistant",
            "content": bot_reply
        })

        message_count += 1

        # Devolver la respuesta de GPT
        return jsonify({
            'reply': bot_reply,
            'current_count': message_count,
            'total_messages': MAX_MESSAGES
        })
    
    except Exception as e:
        print(e)
        return 'Error en la comunicación con el servidor. Por favor, intenta de nuevo más tarde.', 500