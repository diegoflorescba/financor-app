import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def add_pagada_field():
    with app.app_context():
        try:
            # Agregar columna pagada a la tabla cuota
            db.session.execute(text('ALTER TABLE cuota ADD COLUMN pagada BOOLEAN NOT NULL DEFAULT FALSE'))
            
            db.session.commit()
            print("Campo pagada agregado exitosamente a la tabla cuota")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al agregar campo pagada: {str(e)}")

if __name__ == '__main__':
    add_pagada_field() 