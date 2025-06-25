import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Prestamo, Cuota, EstadoPrestamo, EstadoCuota

def update_estados():
    with app.app_context():
        # Actualizar estados de préstamos
        for prestamo in Prestamo.query.all():
            if prestamo.proceso_judicial:
                prestamo.estado = EstadoPrestamo.JUDICIAL
            elif all(cuota.pagada for cuota in prestamo.cuotas):
                prestamo.estado = EstadoPrestamo.FINALIZADO
            else:
                prestamo.estado = EstadoPrestamo.ACTIVO

        # Actualizar estados de cuotas
        for cuota in Cuota.query.all():
            if cuota.prestamo.estado == EstadoPrestamo.JUDICIAL:
                cuota.estado = EstadoCuota.JUDICIAL
            elif cuota.pagada:
                cuota.estado = EstadoCuota.PAGADA
            elif cuota.monto_pagado > 0:
                cuota.estado = EstadoCuota.PAGO_PARCIAL
            else:
                cuota.estado = EstadoCuota.PENDIENTE

        db.session.commit()

if __name__ == '__main__':
    update_estados() 