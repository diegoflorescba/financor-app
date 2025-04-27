import sqlite3
import os
from app import app
from models import User, db

def check_database_structure():
    """Verificar la estructura de la base de datos"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'prestamos.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== Estructura de la tabla user ===")
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    for column in columns:
        print(f"Columna: {column[1]}, Tipo: {column[2]}, Nullable: {not column[3]}")
    
    conn.close()

def check_user_data():
    """Verificar los datos de usuarios"""
    with app.app_context():
        print("\n=== Datos de usuarios ===")
        users = User.query.all()
        for user in users:
            print(f"\nUsuario ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Is Active: {user.is_active}")
            print(f"Created At: {user.created_at}")
            print("-" * 30)

if __name__ == '__main__':
    print("Iniciando verificación de la base de datos...")
    check_database_structure()
    check_user_data()
    print("\nVerificación completada") 