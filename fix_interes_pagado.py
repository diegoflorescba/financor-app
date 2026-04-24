#!/usr/bin/env python3
"""
Script para corregir los valores nulos en el campo interes_pagado de la tabla Pago.
"""

import sys
import os
from datetime import datetime

# Agregar el directorio actual al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Pago

def fix_interes_pagado():
    """
    Actualiza todos los registros que tienen interes_pagado como NULL a 0.0
    """
    with app.app_context():
        print("Iniciando corrección de valores nulos en interes_pagado...")
        
        # Obtener todos los pagos con interes_pagado nulo
        pagos_nulos = Pago.query.filter(Pago.interes_pagado.is_(None)).all()
        
        print(f"Encontrados {len(pagos_nulos)} pagos con interés nulo")
        
        # Actualizar cada pago
        for pago in pagos_nulos:
            try:
                pago.interes_pagado = 0.0
                print(f"  Actualizando pago ID {pago.id_pago}")
            except Exception as e:
                print(f"  Error actualizando pago {pago.id_pago}: {str(e)}")
                continue
        
        # Confirmar cambios
        try:
            db.session.commit()
            print("\n✅ Actualización completada exitosamente!")
            print(f"   {len(pagos_nulos)} pagos actualizados")
        except Exception as e:
            print(f"\n❌ Error al confirmar cambios: {str(e)}")
            db.session.rollback()
            return False
        
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("CORRECCIÓN DE INTERÉS PAGADO")
    print("=" * 60)
    
    if fix_interes_pagado():
        print("\nProceso completado correctamente.")
    else:
        print("\nEl proceso falló.")
        sys.exit(1) 