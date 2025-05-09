import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from flask import Flask
from models import db
from sqlalchemy import text

def run_migration():
    app = Flask(__name__)
    
    # Configuración de la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'prestamos.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Add new columns one by one to handle SQLite limitations
            for column in [
                "monto_original DECIMAL(10,2)",
                "monto_pendiente DECIMAL(10,2)",
                "interes_acumulado DECIMAL(10,2) DEFAULT 0.0",
                "fecha_ultimo_pago DATETIME",
                "ajuste_manual DECIMAL(10,2)",
                "nota_ajuste TEXT"
            ]:
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE cuota ADD COLUMN {column};"))
                    print(f"Added column: {column}")
                except Exception as e:
                    print(f"Column might already exist or error: {str(e)}")
            
            # Update existing records
            with db.engine.connect() as conn:
                conn.execute(text('''
                    UPDATE cuota 
                    SET monto_original = monto,
                        monto_pendiente = CASE 
                            WHEN pagada = 1 THEN 0 
                            ELSE monto - COALESCE(monto_pagado, 0) 
                        END,
                        interes_acumulado = 0.0,
                        fecha_ultimo_pago = CASE 
                            WHEN pagada = 1 THEN fecha_pago 
                            ELSE NULL 
                        END;
                '''))
                conn.commit()
            
            print("Migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            raise e

if __name__ == '__main__':
    run_migration() 