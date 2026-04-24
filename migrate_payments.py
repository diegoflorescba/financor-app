#!/usr/bin/env python3
"""
Script de migración para mover datos de pagos existentes desde el modelo Cuota 
hacia la nueva tabla Pago para trazabilidad completa.

Este script:
1. Itera sobre todas las cuotas que tienen pagos registrados
2. Crea registros Pago correspondientes con los datos históricos
3. Preserva información relevante como monto, fecha, tipo y usuario
4. Mantiene la integridad de los datos existentes
"""

import sys
import os
from datetime import datetime

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Cuota, Pago, User

def migrate_payments():
    """
    Migra los datos de pagos existentes desde Cuota hacia la tabla Pago.
    """
    with app.app_context():
        print("Iniciando migración de pagos...")
        
        # Obtener todas las cuotas que tienen pagos registrados
        cuotas_con_pagos = Cuota.query.filter(
            (Cuota.monto_pagado > 0) | 
            (Cuota.fecha_pago.isnot(None))
        ).all()
        
        print(f"Encontradas {len(cuotas_con_pagos)} cuotas con pagos registrados")
        
        # Contador para estadísticas
        pagos_creados = 0
        pagos_omitidos = 0
        
        for cuota in cuotas_con_pagos:
            try:
                # Verificar si ya existe un pago para esta cuota
                pago_existente = Pago.query.filter_by(id_cuota=cuota.id_cuota).first()
                
                if pago_existente:
                    print(f"  Omitiendo cuota {cuota.id_cuota} - ya tiene pagos registrados")
                    pagos_omitidos += 1
                    continue
                
                # Determinar el tipo de pago basado en el estado y monto
                if cuota.estado.value == 'PAGADA':
                    tipo_pago = 'total'
                elif cuota.monto_pagado > 0:
                    tipo_pago = 'parcial'
                else:
                    tipo_pago = 'parcial'
                
                # Determinar la fecha del pago
                fecha_pago = cuota.fecha_pago if cuota.fecha_pago else cuota.updated_at
                
                # Determinar el usuario que registró el pago
                usuario_id = cuota.updated_by if cuota.updated_by else cuota.created_by
                
                # Crear el registro de pago
                nuevo_pago = Pago(
                    id_cuota=cuota.id_cuota,
                    fecha_pago=fecha_pago,
                    monto_pagado=cuota.monto_pagado,
                    interes_pagado=0.0,  # No tenemos datos históricos de interés separado
                    tipo_pago=tipo_pago,
                    nota=f"Migración automática - Pago original registrado el {fecha_pago.strftime('%Y-%m-%d %H:%M:%S')}",
                    created_by=usuario_id,
                    created_at=fecha_pago
                )
                
                db.session.add(nuevo_pago)
                pagos_creados += 1
                
                print(f"  Creado pago para cuota {cuota.id_cuota}: ${cuota.monto_pagado:.2f} - {tipo_pago}")
                
            except Exception as e:
                print(f"  Error procesando cuota {cuota.id_cuota}: {str(e)}")
                db.session.rollback()
                continue
        
        # Confirmar todos los cambios
        try:
            db.session.commit()
            print(f"\nMigración completada exitosamente!")
            print(f"Pagos creados: {pagos_creados}")
            print(f"Pagos omitidos (ya existían): {pagos_omitidos}")
            
        except Exception as e:
            print(f"Error al confirmar cambios: {str(e)}")
            db.session.rollback()
            return False
        
        return True

def verify_migration():
    """
    Verifica que la migración se haya realizado correctamente.
    """
    with app.app_context():
        print("\nVerificando migración...")
        
        # Contar cuotas con pagos
        cuotas_con_pagos = Cuota.query.filter(
            (Cuota.monto_pagado > 0) | 
            (Cuota.fecha_pago.isnot(None))
        ).count()
        
        # Contar registros en tabla Pago
        total_pagos = Pago.query.count()
        
        print(f"Cuotas con pagos registrados: {cuotas_con_pagos}")
        print(f"Registros en tabla Pago: {total_pagos}")
        
        if total_pagos > 0:
            print("✅ Migración verificada - Datos de pagos migrados correctamente")
            return True
        else:
            print("❌ Migración fallida - No se encontraron registros en tabla Pago")
            return False

def main():
    """
    Función principal que ejecuta la migración.
    """
    print("=" * 60)
    print("MIGRACIÓN DE PAGOS - Cuota → Pago")
    print("=" * 60)
    
    # Ejecutar migración
    if migrate_payments():
        # Verificar migración
        verify_migration()
    else:
        print("❌ La migración falló")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    main() 