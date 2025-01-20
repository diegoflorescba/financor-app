#!/bin/bash

# Activar el entorno virtual
source venv/bin/activate

# Establecer variables de entorno si es necesario
export FLASK_APP=app.py
export FLASK_ENV=development

# Iniciar la aplicación
python3 app.py