import os
from flask import Flask
from models import db, User
from sqlalchemy import text

def migrate_db():
    """Migra la base de datos para usar contraseñas en texto plano"""
    app = Flask(__name__)
    
    # Configurar la ruta de la base de datos
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'prestamos.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Renombrar la columna password_hash a password
            db.session.execute(text("ALTER TABLE user RENAME COLUMN password_hash TO password"))
            db.session.commit()
            print("Base de datos migrada exitosamente")
            
            # Crear usuario admin si no existe
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    role='admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Usuario admin creado:")
                print("Usuario: admin")
                print("Contraseña: admin123")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la migración: {str(e)}")
            print("Creando nueva base de datos...")
            
            # Si hay error, eliminar y recrear la base de datos
            db.drop_all()
            db.create_all()
            
            # Crear usuario admin
            admin = User(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Nueva base de datos creada con usuario admin:")
            print("Usuario: admin")
            print("Contraseña: admin123")

if __name__ == '__main__':
    migrate_db()