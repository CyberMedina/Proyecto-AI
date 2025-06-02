from werkzeug.security import check_password_hash, generate_password_hash

def cifrar_string(texto):
    """Cifra un string usando generate_password_hash."""
    return generate_password_hash(texto)

def verificar_string(texto, hash_cifrado):
    """Verifica si un string coincide con el hash cifrado."""
    return check_password_hash(hash_cifrado, texto)

if __name__ == "__main__":
    # Solicitar al usuario un string para cifrar
    texto = input("Introduce un texto para cifrar: ")
    hash_cifrado = cifrar_string(texto)
    print(f"Texto cifrado: {hash_cifrado}")
    
    # Verificar el texto ingresado
    texto_verificacion = input("Introduce el texto nuevamente para verificar: ")
    if verificar_string(texto_verificacion, hash_cifrado):
        print("El texto coincide con el hash cifrado.")
    else:
        print("El texto no coincide con el hash cifrado.")