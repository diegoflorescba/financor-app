import os
from app import app, db

def init_database():
    db_path = 'instance/prestamos.db'
    
    # Verificar si la base de datos ya existe
    if os.path.exists(db_path):
        print("La base de datos ya existe. No se realizará la inicialización.")
        return False
    
    # Si no existe, crear la carpeta instance si es necesario
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # Crear la base de datos y las tablas
    with app.app_context():
        db.create_all()
        print("Base de datos inicializada correctamente.")
        return True

if __name__ == '__main__':
    init_database()