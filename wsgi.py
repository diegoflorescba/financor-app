import os
import sys

# Agregar el directorio actual al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

# Configurar el puerto para Render
port = int(os.environ.get('PORT', 10000))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port) 