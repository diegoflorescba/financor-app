# Instructivo de Migración: Actualizar develop con cambios de develop-dev

> **IMPORTANTE:** Antes de ejecutar cualquier paso, realiza un backup de la base de datos actual (`prestamos.db`).

---

## 1. Respaldo de la base de datos

```sh
cp prestamos_app/instance/prestamos.db prestamos_app/instance/prestamos_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## 2. Actualización del código

```sh
git fetch
git checkout develop-dev # O haz merge de develop-dev en develop si prefieres mantener develop como principal
git pull
```

---

## 3. Migración de la base de datos

Ejecuta los siguientes scripts **en este orden** desde la carpeta `prestamos_app/`:

### a) Agregar nuevas columnas a la tabla cuota
```sh
python3 migrations/add_cuota_columns.py
```

### b) Agregar campo pagada a cuota
```sh
python3 migrations/add_pagada_field.py
```

### c) Agregar campo proceso_judicial a prestamo y cuota
```sh
python3 migrations/add_proceso_judicial.py
```

### d) Migrar los pagos históricos a la nueva tabla Pago
```sh
python3 migrate_payments.py
```

### e) Corregir valores nulos en interes_pagado
```sh
python3 fix_interes_pagado.py
```

### f) Actualizar estados de préstamos y cuotas
```sh
python3 migrations/update_estados.py
```

### g) Verificar la migración
```sh
python3 verify_migration.py
```

---

## 4. Verificación y pruebas

- Revisa la salida de los scripts, especialmente el de verificación.
- Navega por la app y prueba las funcionalidades principales.
- Si ocurre un error, restaura el backup realizado al inicio.

---

## 5. Notas y recomendaciones

- No elimines los scripts de migración hasta confirmar que todo funciona correctamente.
- Si la base de datos es muy grande, ejecuta los scripts en horarios de bajo uso.
- Documenta cualquier cambio manual realizado.

---

**Ante cualquier duda, consulta con el equipo de desarrollo antes de proceder.** 