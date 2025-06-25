#!/usr/bin/env python3
"""
Script de verificación para mostrar los datos migrados y confirmar 
que la migración de pagos fue exitosa.
"""

import sys
import os
from datetime import datetime

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Cuota, Pago, User, Prestamo, Cliente

def show_migration_summary():
    """
    Muestra un resumen de la migración realizada.
    """
    with app.app_context():
        print("=" * 80)
        print("VERIFICACIÓN DE MIGRACIÓN DE PAGOS")
        print("=" * 80)
        
        # Estadísticas generales
        total_cuotas = Cuota.query.count()
        cuotas_con_pagos = Cuota.query.filter(
            (Cuota.monto_pagado > 0) | 
            (Cuota.fecha_pago.isnot(None))
        ).count()
        total_pagos = Pago.query.count()
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   • Total de cuotas en el sistema: {total_cuotas}")
        print(f"   • Cuotas con pagos registrados: {cuotas_con_pagos}")
        print(f"   • Registros en tabla Pago: {total_pagos}")
        print()
        
        # Verificar integridad
        print(f"🔍 VERIFICACIÓN DE INTEGRIDAD:")
        if total_pagos == cuotas_con_pagos:
            print("   ✅ Todos los pagos fueron migrados correctamente")
        else:
            print("   ❌ Hay discrepancias en la migración")
        print()
        
        # Mostrar algunos ejemplos de pagos migrados
        print(f"📋 EJEMPLOS DE PAGOS MIGRADOS:")
        pagos_ejemplo = Pago.query.limit(10).all()
        
        for pago in pagos_ejemplo:
            cuota = pago.cuota
            prestamo = cuota.prestamo
            cliente = prestamo.cliente
            
            print(f"   • Pago ID {pago.id_pago}: ${pago.monto_pagado:,.2f}")
            print(f"     - Cliente: {cliente.nombre} {cliente.apellido}")
            print(f"     - Cuota: {cuota.numero_cuota} del préstamo {prestamo.id_prestamo}")
            print(f"     - Tipo: {pago.tipo_pago}")
            print(f"     - Fecha: {pago.fecha_pago.strftime('%Y-%m-%d %H:%M')}")
            print(f"     - Nota: {pago.nota}")
            print()
        
        # Resumen por tipo de pago
        print(f"📈 RESUMEN POR TIPO DE PAGO:")
        pagos_totales = Pago.query.filter_by(tipo_pago='total').count()
        pagos_parciales = Pago.query.filter_by(tipo_pago='parcial').count()
        
        print(f"   • Pagos totales: {pagos_totales}")
        print(f"   • Pagos parciales: {pagos_parciales}")
        print()
        
        # Monto total migrado
        monto_total = db.session.query(db.func.sum(Pago.monto_pagado)).scalar() or 0
        print(f"💰 MONTO TOTAL MIGRADO: ${monto_total:,.2f}")
        print()
        
        print("=" * 80)
        print("VERIFICACIÓN COMPLETADA")
        print("=" * 80)

if __name__ == "__main__":
    show_migration_summary() 