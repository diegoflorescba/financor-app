import os
import sqlite3
import shutil
from datetime import datetime
from app import app
from models import db
from sqlalchemy import text

def backup_database():
    """Crear una copia de seguridad de la base de datos"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'prestamos.db')
    backup_path = os.path.join(basedir, 'instance', f'prestamos_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"Backup creado en: {backup_path}")
    else:
        print("No se encontró la base de datos para hacer backup")

def check_password_column():
    """Verificar si la columna password existe en la tabla user"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'prestamos.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener información sobre las columnas de la tabla user
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    
    has_password = any(column[1] == 'password' for column in columns)
    conn.close()
    
    return has_password

def migrate_password_column():
    """Migrar la estructura de la base de datos para agregar la columna password"""
    with app.app_context():
        try:
            # Verificar si la columna ya existe
            if check_password_column():
                print("La columna password ya existe en la tabla user")
                return
            
            # Crear una tabla temporal con la nueva estructura
            db.session.execute(text('''
                CREATE TABLE user_temp (
                    id INTEGER NOT NULL PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    email VARCHAR(120),
                    password VARCHAR(128),
                    role VARCHAR(20) NOT NULL,
                    is_active BOOLEAN,
                    created_at DATETIME,
                    last_login DATETIME,
                    created_by INTEGER,
                    updated_by INTEGER,
                    FOREIGN KEY(created_by) REFERENCES user (id),
                    FOREIGN KEY(updated_by) REFERENCES user (id)
                )
            '''))
            
            # Copiar los datos existentes
            db.session.execute(text('''
                INSERT INTO user_temp (
                    id, username, email, role, is_active, 
                    created_at, last_login, created_by, updated_by
                )
                SELECT 
                    id, username, email, role, is_active,
                    created_at, last_login, created_by, updated_by
                FROM user
            '''))
            
            # Eliminar la tabla original
            db.session.execute(text('DROP TABLE user'))
            
            # Renombrar la tabla temporal
            db.session.execute(text('ALTER TABLE user_temp RENAME TO user'))
            
            db.session.commit()
            print("Migración completada exitosamente")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error durante la migración: {str(e)}")
            raise

if __name__ == '__main__':
    print("Iniciando proceso de migración...")
    backup_database()
    migrate_password_column()
    print("Proceso de migración finalizado") 