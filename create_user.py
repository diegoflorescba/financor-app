from app import app, db
from models import User

def create_readonly_user(username, email, password):
    with app.app_context():
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"El usuario {username} ya existe")
            return
        
        # Crear nuevo usuario con rol 'user' (solo lectura)
        user = User(
            username=username,
            email=email,
            role='user',  # rol de solo lectura
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        print(f"Usuario {username} creado exitosamente con permisos de solo lectura")

if __name__ == '__main__':
    # Crear usuario de solo lectura
    create_readonly_user(
        username='pablovillagra',
        email='pablovillagra@gmail.com',
        password='pablovillagra123.'
    ) 