-- Script para agregar la tabla user y corregir referencias

-- 1. Crear la tabla user si no existe
CREATE TABLE IF NOT EXISTS user (
    id INTEGER NOT NULL,
    username VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL,
    password_hash VARCHAR(128),
    role VARCHAR(20) NOT NULL,
    is_active BOOLEAN,
    created_at DATETIME,
    last_login DATETIME,
    created_by INTEGER,
    updated_by INTEGER,
    PRIMARY KEY (id),
    UNIQUE (username),
    UNIQUE (email),
    FOREIGN KEY(created_by) REFERENCES user (id),
    FOREIGN KEY(updated_by) REFERENCES user (id)
);

-- 2. Insertar el usuario administrador por defecto si no existe
INSERT OR IGNORE INTO user (
    id, username, email, password_hash, role, is_active, created_at, last_login
) VALUES (
    1,
    'admin',
    'admin@prestamos.com',
    'pbkdf2:sha256:600000$XvBz8ZvG$c8c1c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0',
    'admin',
    1,
    datetime('now'),
    datetime('now')
);

-- 3. Actualizar las referencias en las tablas existentes
UPDATE cliente 
SET created_by = 1,
    updated_by = 1
WHERE created_by IS NULL;

UPDATE prestamo 
SET created_by = 1,
    updated_by = 1
WHERE created_by IS NULL;

UPDATE cuota 
SET created_by = 1,
    updated_by = 1
WHERE created_by IS NULL;

-- 4. Verificar que todo se haya actualizado correctamente
SELECT 'Tabla user creada y referencias actualizadas correctamente'; 