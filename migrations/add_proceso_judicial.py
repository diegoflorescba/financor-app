import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Prestamo, Cuota
from sqlalchemy import text

def upgrade():
    with app.app_context():
        # Agregar columna proceso_judicial a la tabla prestamo
        db.session.execute(text('ALTER TABLE prestamo ADD COLUMN proceso_judicial BOOLEAN NOT NULL DEFAULT FALSE'))
        
        # Agregar columna proceso_judicial a la tabla cuota
        db.session.execute(text('ALTER TABLE cuota ADD COLUMN proceso_judicial BOOLEAN NOT NULL DEFAULT FALSE'))
        
        db.session.commit()

def downgrade():
    with app.app_context():
        # Eliminar columna proceso_judicial de la tabla cuota
        db.session.execute(text('ALTER TABLE cuota DROP COLUMN proceso_judicial'))
        
        # Eliminar columna proceso_judicial de la tabla prestamo
        db.session.execute(text('ALTER TABLE prestamo DROP COLUMN proceso_judicial'))
        
        db.session.commit()

if __name__ == '__main__':
    upgrade() 