# OilWise: Recomendaciones expertas

OilWise es una aplicación desarrollada con Flask, Python y MySQL que busca proporcionar soluciones inteligentes en el ámbito de la industria de lubricentros.

## Pre-requisitos

- Python 3.6 o superior.
- PIP (Gestor de paquetes de Python).
- MySQL.

## Configuración del Entorno

### Creación del entorno virtual

Para crear un entorno virtual y aislar las dependencias necesarias, ejecute el siguiente comando en la raíz del proyecto:

```bash
python -m venv env
```
### Activación del entorno virtual

Active el entorno virtual utilizando el siguiente comando:

```bash
.\env\Scripts\activate
```

### Instalación de las dependencias

Instale las dependencias necesarias para ejecutar OilWise con el siguiente comando:

```bash
pip install -r requirements.txt
```

## Configuración de la Base de Datos

Antes de ejecutar el proyecto, asegúrese de haber ejecutado el script de la base de datos y configurado la conexión a la base de datos correctamente. Puede modificar la configuración de la base de datos en el archivo `config.py`:

```python
# Función para establecer conexión en la base de datos
def connectionBD():
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="1233456",
        database="proyectoia"
    )
    return db
```

## Ejecución del Proyecto

Con todo configurado, ahora está listo para ejecutar el proyecto. Asegúrese de que el entorno virtual esté activado y ejecute el siguiente comando en la raíz del proyecto:

```bash
python app.py
```

Con esto, OilWise debería estar ejecutándose en su máquina local. Para ejecutar el proyecto en el futuro, simplemente active el entorno virtual y ejecute el comando anterior nuevamente.

## Para Ejecutar el Proyecto de Nuevo

Si deseas ejecutar el proyecto nuevamente en el futuro, simplemente sigue estos pasos:

1. Asegúrate de que tu base de datos esté corriendo y la configuración en `config.py` sea la correcta.

2. Activa el entorno virtual (si no está activo) con el siguiente comando:

```bash
.\env\Scripts\activate
```

3. Ejecuta el proyecto con el siguiente comando:

```bash
python app.py
```

---

Si tienes alguna pregunta o encuentras algún problema, no dudes en abrir un issue en GitHub. ¡Gracias por usar OilWise!
## Créditos

Este proyecto fue desarrollado por:

- Bumbul
- Rada
- Ing. Medina

---

Si tienes alguna pregunta o encuentras algún problema, no dudes en abrir un issue en GitHub. ¡Gracias por usar OilWise!

