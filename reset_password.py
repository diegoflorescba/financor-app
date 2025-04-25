from app import app, db
from models import User

def reset_user_password(username, new_password):
    with app.app_context():
        try:
            # Buscar el usuario
            user = User.query.filter_by(username=username).first()
            
            if not user:
                print(f"Error: No se encontró el usuario '{username}'")
                return
            
            # Resetear la contraseña
            user.set_password(new_password)
            db.session.commit()
            
            print(f"Contraseña reseteada exitosamente para el usuario: {username}")
            print(f"Nueva contraseña: {new_password}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al resetear la contraseña: {str(e)}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Uso: python reset_password.py <username> <new_password>")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    reset_user_password(username, new_password) 