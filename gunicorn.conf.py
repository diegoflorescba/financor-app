import os
import multiprocessing

# Configuración del servidor
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 4  # Número fijo de workers para evitar problemas en Render
threads = 2
worker_class = 'sync'
timeout = 120  # Aumentado para dar más tiempo
keepalive = 2

# Asegurarnos de que estamos en el directorio correcto
chdir = os.path.dirname(os.path.abspath(__file__))
pythonpath = chdir

# Configuración de logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configuración adicional
preload_app = True
forwarded_allow_ips = '*' 