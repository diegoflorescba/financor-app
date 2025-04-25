from app import app, db
from models import User
import json
from datetime import datetime

def backup_data():
    """Respalda los datos de la base de datos"""
    with app.app_context():
        users = User.query.all()
        user_data = []
        for user in users:
            user_data.append({
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
        
        with open('prestamos_app/backup_data.json', 'w') as f:
            json.dump(user_data, f, indent=2)
        print("Datos respaldados exitosamente")

def restore_data():
    """Restaura los datos desde el respaldo"""
    with app.app_context():
        try:
            with open('prestamos_app/backup_data.json', 'r') as f:
                user_data = json.load(f)
            
            for data in user_data:
                user = User(
                    username=data['username'],
                    email=data['email'],
                    password_hash=data['password_hash'],
                    role=data['role'],
                    is_active=data['is_active'],
                    created_at=datetime.fromisoformat(data['created_at']) if data['created_at'] else None,
                    last_login=datetime.fromisoformat(data['last_login']) if data['last_login'] else None
                )
                db.session.add(user)
            
            db.session.commit()
            print("Datos restaurados exitosamente")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al restaurar datos: {str(e)}")
            raise e

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ['backup', 'restore']:
        print("Uso: python backup_restore.py [backup|restore]")
        sys.exit(1)
    
    if sys.argv[1] == 'backup':
        backup_data()
    else:
        restore_data() 