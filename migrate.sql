-- Script de migración de prestamos_backup_20250414_064528.db a prestamos.db
-- Primero, creamos un backup de la nueva base de datos
ATTACH DATABASE 'instance/prestamos_backup_20250414_064528.db' AS old_db;
ATTACH DATABASE 'instance/prestamos.db' AS new_db;

-- 1. Migración de la tabla cliente
INSERT INTO new_db.cliente (
    id_cliente, nombre, apellido, dni, telefono, correo_electronico,
    direccion, documentacion_verificada, fecha_registro, activo,
    created_at, updated_at, created_by, updated_by
)
SELECT 
    id_cliente, nombre, apellido, dni, telefono, correo_electronico,
    direccion, documentacion_verificada, fecha_registro, activo,
    fecha_registro, fecha_registro, 1, 1
FROM old_db.cliente;

-- 2. Migración de la tabla garante
INSERT INTO new_db.garante (
    id_garante, nombre, apellido, dni, telefono, correo_electronico,
    direccion, documentacion_verificada, activo
)
SELECT 
    id_garante, nombre, apellido, dni, telefono, correo_electronico,
    direccion, documentacion_verificada, activo
FROM old_db.garante;

-- 3. Migración de la tabla prestamo
INSERT INTO new_db.prestamo (
    id_prestamo, id_cliente, id_garante, monto_prestado, tasa_interes,
    cuotas_totales, cuotas_pendientes, monto_cuotas, monto_adeudado,
    fecha_inicio, fecha_finalizacion, estado, fecha_ultima_actualizacion,
    created_at, updated_at, created_by, updated_by
)
SELECT 
    id_prestamo, id_cliente, id_garante, monto_prestado, tasa_interes,
    cuotas_totales, cuotas_pendientes, monto_cuotas, monto_adeudado,
    fecha_inicio, fecha_finalizacion, estado, fecha_ultima_actualizacion,
    fecha_inicio, fecha_ultima_actualizacion, 1, 1
FROM old_db.prestamo;

-- 4. Migración de la tabla cuota
INSERT INTO new_db.cuota (
    id_cuota, id_prestamo, numero_cuota, fecha_vencimiento, fecha_pago,
    monto, monto_pagado, pagada, estado, created_at, updated_at,
    created_by, updated_by
)
SELECT 
    id_cuota, id_prestamo, numero_cuota, fecha_vencimiento, fecha_pago,
    monto, monto_pagado, pagada, estado,
    COALESCE(fecha_pago, fecha_vencimiento),
    COALESCE(fecha_pago, fecha_vencimiento),
    1, 1
FROM old_db.cuota;

-- Verificación de la migración
SELECT 'Cliente count:', (SELECT COUNT(*) FROM old_db.cliente), 'vs', (SELECT COUNT(*) FROM new_db.cliente);
SELECT 'Garante count:', (SELECT COUNT(*) FROM old_db.garante), 'vs', (SELECT COUNT(*) FROM new_db.garante);
SELECT 'Prestamo count:', (SELECT COUNT(*) FROM old_db.prestamo), 'vs', (SELECT COUNT(*) FROM new_db.prestamo);
SELECT 'Cuota count:', (SELECT COUNT(*) FROM old_db.cuota), 'vs', (SELECT COUNT(*) FROM new_db.cuota);

-- Desconectar las bases de datos
DETACH DATABASE old_db;
DETACH DATABASE new_db; 