import sys
import os

# Activar el entorno virtual
VIRTUALENV = '/home/diegoaflores/.virtualenvs/prestamos_env'
activate_this = os.path.join(VIRTUALENV, 'bin/activate_this.py')
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Path a tu aplicación
path = '/home/diegoaflores/financor-app'
if path not in sys.path:
    sys.path.append(path)

# Configurar variables de entorno
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py'

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Importar la aplicación
from app import app as application

# Configurar la aplicación para producción
application.config['SESSION_COOKIE_SECURE'] = True
application.config['SESSION_COOKIE_HTTPONLY'] = True
application.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
application.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora 