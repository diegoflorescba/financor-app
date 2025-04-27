from app import app, db
from models import User

def create_user(username, password, email=None, role='user'):
    with app.app_context():
        try:
            # Verificar si el usuario ya existe
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"Error: El usuario '{username}' ya existe")
            return

            # Crear nuevo usuario
            user = User(
                username=username,
                email=email or f"{username}@example.com",
                role=role,
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            print(f"Usuario creado exitosamente")
            print(f"Usuario: {username}")
            print(f"Rol: {role}")
            print(f"Contraseña: {password}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear el usuario: {str(e)}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Uso: python create_admin.py <username> <password> [email] [role]")
        print("Ejemplo: python create_admin.py juan password123 juan@email.com admin")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3] if len(sys.argv) > 3 else None
    role = sys.argv[4] if len(sys.argv) > 4 else 'user'
    
    create_user(username, password, email, role) 