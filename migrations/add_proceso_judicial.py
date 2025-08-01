import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Prestamo, Cuota
from sqlalchemy import text

def upgrade():
    with app.app_context():
        try:
            # Agregar columna proceso_judicial a la tabla prestamo
            db.session.execute(text('ALTER TABLE prestamo ADD COLUMN proceso_judicial BOOLEAN NOT NULL DEFAULT FALSE'))
            # Agregar columna proceso_judicial a la tabla cuota
            db.session.execute(text('ALTER TABLE cuota ADD COLUMN proceso_judicial BOOLEAN NOT NULL DEFAULT FALSE'))
            db.session.commit()
            print("Columnas proceso_judicial agregadas exitosamente")
        except Exception as e:
            db.session.rollback()
            print(f"Error al agregar columnas proceso_judicial: {str(e)}")

def downgrade():
    with app.app_context():
        try:
            # Eliminar columna proceso_judicial de la tabla cuota
            db.session.execute(text('ALTER TABLE cuota DROP COLUMN proceso_judicial'))
            # Eliminar columna proceso_judicial de la tabla prestamo
            db.session.execute(text('ALTER TABLE prestamo DROP COLUMN proceso_judicial'))
            db.session.commit()
            print("Columnas proceso_judicial eliminadas exitosamente")
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar columnas proceso_judicial: {str(e)}")

if __name__ == '__main__':
    upgrade() 