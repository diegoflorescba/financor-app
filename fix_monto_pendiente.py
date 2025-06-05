from app import app
from models import db, Cuota

with app.app_context():
    cuotas = Cuota.query.all()
    for cuota in cuotas:
        cuota.monto_pendiente = cuota.monto - cuota.monto_pagado
    db.session.commit()

print('Todos los montos pendientes han sido corregidos.') 