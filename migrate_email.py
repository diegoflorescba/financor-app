from app import app
from models import db
from sqlalchemy import text

def migrate_email_field():
    with app.app_context():
        # Modificar la columna email para hacerla nullable
        db.session.execute(text('ALTER TABLE user RENAME TO user_old'))
        db.create_all()  # Esto creará la nueva tabla con la estructura actualizada
        db.session.execute(text('''
            INSERT INTO user (id, username, email, password, role, is_active, created_at, last_login, created_by, updated_by)
            SELECT id, username, email, password, role, is_active, created_at, last_login, created_by, updated_by
            FROM user_old
        '''))
        db.session.execute(text('DROP TABLE user_old'))
        db.session.commit()
        print("Migración completada exitosamente")

if __name__ == '__main__':
    migrate_email_field() 