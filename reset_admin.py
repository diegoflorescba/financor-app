from app import app, db
from models import User

def reset_admin():
    with app.app_context():
        try:
            # Eliminar todos los usuarios admin existentes
            User.query.filter_by(role='admin').delete()
            
            # Crear nuevo usuario admin
            admin = User(
                username='fedemartinez',
                email='fedemartinez@gmail.com',
                role='admin',
                is_active=True
            )
            admin.set_password('imogenes123')
            
            db.session.add(admin)
            db.session.commit()
            print(f"Usuario admin creado exitosamente")
            print(f"Usuario: {admin.username}")
            print(f"Contraseña: {admin.password_hash}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al reiniciar el usuario admin: {str(e)}")

if __name__ == '__main__':
    reset_admin() 