import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db, app
from models import Prestamo, Cuota, EstadoPrestamo, EstadoCuota
from datetime import datetime

def fix_judicial_loans():
    print("Iniciando corrección de préstamos judiciales...")
    try:
        with app.app_context():
            # Encontrar préstamos con todas las cuotas judiciales
            prestamos = Prestamo.query.all()
            actualizados = 0
            
            for prestamo in prestamos:
                total_cuotas = len(prestamo.cuotas)
                cuotas_judicial = sum(1 for c in prestamo.cuotas if c.estado == EstadoCuota.JUDICIAL)
                
                # Si todas las cuotas son judiciales pero el préstamo no
                if total_cuotas > 0 and total_cuotas == cuotas_judicial:
                    print(f"Actualizando préstamo {prestamo.id_prestamo}...")
                    print(f"- Estado anterior: {prestamo.estado.name}")
                    print(f"- Cuotas totales: {total_cuotas}")
                    print(f"- Cuotas judiciales: {cuotas_judicial}")
                    
                    # Calcular monto adeudado usando el monto total de las cuotas judiciales
                    monto_adeudado = sum(c.monto for c in prestamo.cuotas if c.estado == EstadoCuota.JUDICIAL)
                    print(f"- Monto adeudado anterior: {prestamo.monto_adeudado}")
                    print(f"- Nuevo monto adeudado: {monto_adeudado}")
                    
                    # Actualizar préstamo
                    prestamo.estado = EstadoPrestamo.JUDICIAL
                    prestamo.proceso_judicial = True
                    prestamo.monto_adeudado = monto_adeudado
                    actualizados += 1
            
            if actualizados > 0:
                db.session.commit()
                print(f"\nSe actualizaron {actualizados} préstamos a estado JUDICIAL")
            else:
                print("\nNo se encontraron préstamos para actualizar")
            
    except Exception as e:
        print(f"Error durante la migración: {str(e)}")
        db.session.rollback()
        raise e

if __name__ == '__main__':
    fix_judicial_loans() 