import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def remove_proceso_judicial():
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
            print(f"Error al eliminar columnas: {str(e)}")

if __name__ == '__main__':
    remove_proceso_judicial() 