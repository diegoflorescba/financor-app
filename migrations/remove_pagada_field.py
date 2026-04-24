import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db, app
from models import Cuota, EstadoCuota

def remove_pagada_field():
    print("Iniciando migración para eliminar campo pagada...")
    try:
        with app.app_context():
            # Crear una tabla temporal sin el campo pagada
            db.session.execute("""
                CREATE TABLE cuota_temp (
                    id_cuota INTEGER PRIMARY KEY,
                    id_prestamo INTEGER NOT NULL,
                    numero_cuota INTEGER NOT NULL,
                    fecha_vencimiento DATETIME NOT NULL,
                    monto FLOAT NOT NULL,
                    monto_pagado FLOAT DEFAULT 0.0,
                    monto_pendiente FLOAT,
                    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
                    fecha_pago DATETIME,
                    nota_ajuste VARCHAR(255),
                    proceso_judicial BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_by INTEGER,
                    FOREIGN KEY(id_prestamo) REFERENCES prestamo(id_prestamo),
                    FOREIGN KEY(created_by) REFERENCES user(id),
                    FOREIGN KEY(updated_by) REFERENCES user(id)
                )
            """)

            # Copiar los datos
            print("Copiando datos a la tabla temporal...")
            db.session.execute("""
                INSERT INTO cuota_temp 
                SELECT id_cuota, id_prestamo, numero_cuota, fecha_vencimiento, 
                       monto, monto_pagado, monto_pendiente, estado, fecha_pago,
                       nota_ajuste, proceso_judicial, created_at, updated_at,
                       created_by, updated_by
                FROM cuota
            """)

            # Eliminar la tabla original
            print("Eliminando tabla original...")
            db.session.execute("DROP TABLE cuota")

            # Renombrar la tabla temporal
            print("Renombrando tabla temporal...")
            db.session.execute("ALTER TABLE cuota_temp RENAME TO cuota")

            db.session.commit()
            print("Migración completada exitosamente")

    except Exception as e:
        print(f"Error durante la migración: {str(e)}")
        db.session.rollback()
        raise e

if __name__ == '__main__':
    remove_pagada_field() 