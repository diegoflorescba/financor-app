import os
from flask import Flask
from models import db, User

def init_db():
    """Inicializa la base de datos y crea el usuario administrador si no existe"""
    app = Flask(__name__)
    
    # Configurar la ruta de la base de datos
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'prestamos.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Asegurar que el directorio de la base de datos existe
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, mode=0o777)
    
    db.init_app(app)
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("Tablas creadas exitosamente")
        
        # Verificar si el usuario admin ya existe
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            try:
                # Crear el usuario admin con contraseña en texto plano
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',  # Contraseña en texto plano
                    role='admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Usuario admin creado exitosamente")
                print("Usuario: admin")
                print("Contraseña: admin123")
            except Exception as e:
                print(f"Error al crear el usuario admin: {str(e)}")
                db.session.rollback()
        else:
            print("El usuario admin ya existe")

if __name__ == '__main__':
    init_db()