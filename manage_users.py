import sys
from app import app, db
from models import User
from datetime import datetime

def list_users():
    """Lista todos los usuarios en la base de datos"""
    with app.app_context():
        users = User.query.all()
        print("\nLista de usuarios:")
        print("=" * 80)
        print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Role':<10} {'Active':<8} {'Created':<20}")
        print("-" * 80)
        for user in users:
            print(f"{user.id:<5} {user.username:<15} {user.email:<25} {user.role:<10} {str(user.is_active):<8} {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

def create_user(username, email, password, role='user'):
    """Crea un nuevo usuario"""
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"Error: El usuario {username} ya existe.")
            return
        if User.query.filter_by(email=email).first():
            print(f"Error: El email {email} ya está registrado.")
            return
        
        user = User(
            username=username,
            email=email,
            role=role,
            is_active=True,
            created_at=datetime.utcnow()
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            print(f"Usuario {username} creado exitosamente.")
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear usuario: {str(e)}")

def change_password(username, new_password):
    """Cambia la contraseña de un usuario"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: Usuario {username} no encontrado.")
            return
        
        try:
            user.set_password(new_password)
            db.session.commit()
            print(f"Contraseña actualizada para el usuario {username}.")
        except Exception as e:
            db.session.rollback()
            print(f"Error al cambiar la contraseña: {str(e)}")

def toggle_user_status(username):
    """Activa/desactiva un usuario"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: Usuario {username} no encontrado.")
            return
        
        try:
            user.is_active = not user.is_active
            db.session.commit()
            status = "activado" if user.is_active else "desactivado"
            print(f"Usuario {username} {status} exitosamente.")
        except Exception as e:
            db.session.rollback()
            print(f"Error al cambiar el estado del usuario: {str(e)}")

def print_help():
    print("""
Uso: python manage_users.py <comando> [argumentos]

Comandos disponibles:
  list                                    Lista todos los usuarios
  create <username> <email> <password> [role]  Crea un nuevo usuario
  password <username> <new_password>      Cambia la contraseña de un usuario
  toggle <username>                       Activa/desactiva un usuario
  help                                    Muestra esta ayuda
""")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print_help()
    elif sys.argv[1] == "list":
        list_users()
    elif sys.argv[1] == "create" and len(sys.argv) >= 5:
        role = sys.argv[5] if len(sys.argv) > 5 else "user"
        create_user(sys.argv[2], sys.argv[3], sys.argv[4], role)
    elif sys.argv[1] == "password" and len(sys.argv) == 4:
        change_password(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "toggle" and len(sys.argv) == 3:
        toggle_user_status(sys.argv[2])
    else:
        print("Error: Comando o argumentos inválidos")
        print_help() 