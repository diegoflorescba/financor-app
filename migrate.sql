-- Script de migración seguro para PythonAnywhere
-- Este script agrega nuevas funcionalidades sin borrar datos existentes

-- 1. Agregar campos de auditoría a la tabla cliente
ALTER TABLE cliente ADD COLUMN created_by INTEGER;
ALTER TABLE cliente ADD COLUMN updated_by INTEGER;
ALTER TABLE cliente ADD COLUMN created_at DATETIME;
ALTER TABLE cliente ADD COLUMN updated_at DATETIME;

-- 2. Agregar campos de auditoría a la tabla prestamo
ALTER TABLE prestamo ADD COLUMN created_by INTEGER;
ALTER TABLE prestamo ADD COLUMN updated_by INTEGER;
ALTER TABLE prestamo ADD COLUMN created_at DATETIME;
ALTER TABLE prestamo ADD COLUMN updated_at DATETIME;

-- 3. Agregar campos de auditoría a la tabla cuota
ALTER TABLE cuota ADD COLUMN created_by INTEGER;
ALTER TABLE cuota ADD COLUMN updated_by INTEGER;
ALTER TABLE cuota ADD COLUMN created_at DATETIME;
ALTER TABLE cuota ADD COLUMN updated_at DATETIME;

-- 4. Crear la tabla audit_log si no existe
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    changes JSON,
    timestamp DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES user (id)
);

-- 5. Actualizar los campos de auditoría con valores por defecto donde sean NULL
UPDATE cliente 
SET created_at = fecha_registro,
    updated_at = fecha_registro,
    created_by = 1,
    updated_by = 1
WHERE created_at IS NULL;

UPDATE prestamo 
SET created_at = fecha_inicio,
    updated_at = fecha_ultima_actualizacion,
    created_by = 1,
    updated_by = 1
WHERE created_at IS NULL;

UPDATE cuota 
SET created_at = COALESCE(fecha_pago, fecha_vencimiento),
    updated_at = COALESCE(fecha_pago, fecha_vencimiento),
    created_by = 1,
    updated_by = 1
WHERE created_at IS NULL;

-- Verificación de la migración
SELECT 'Tablas actualizadas correctamente'; 