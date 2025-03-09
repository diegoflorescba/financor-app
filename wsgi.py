import sys
import os

# Agregar el directorio del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prestamos_app.app import app

if __name__ == "__main__":
    app.run() 