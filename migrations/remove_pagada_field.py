import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def remove_pagada_field():
    with app.app_context():
        try:
            # Eliminar columna pagada de la tabla cuota
            db.session.execute(text('ALTER TABLE cuota DROP COLUMN pagada'))
            
            db.session.commit()
            print("Campo pagada eliminado exitosamente de la tabla cuota")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar campo pagada: {str(e)}")

if __name__ == '__main__':
    remove_pagada_field() 