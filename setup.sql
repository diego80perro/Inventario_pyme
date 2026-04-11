-- ============================================================
-- Inventario PYME - Script de base de datos MySQL
-- Ejecutar: mysql -u root -p < setup.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS pyme_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pyme_db;

CREATE TABLE IF NOT EXISTS productos (
    id      INT          AUTO_INCREMENT PRIMARY KEY,
    codigo  VARCHAR(50)  NOT NULL UNIQUE,
    nombre  VARCHAR(200) NOT NULL,
    precio  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock   INT          NOT NULL DEFAULT 0,
    creado  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_nombre (nombre),
    INDEX idx_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Datos de ejemplo (opcional, puedes borrar este bloque)
INSERT IGNORE INTO productos (codigo, nombre, precio, stock) VALUES
  ('P001', 'Cuaderno universitario', 3.50, 120),
  ('P002', 'Bolígrafo azul x12',     5.99,  45),
  ('P003', 'Resma de papel A4',       8.00,   3),
  ('P004', 'Carpeta de argollas',     4.25,  60),
  ('P005', 'Marcadores de colores',   6.80,   2);

SELECT 'Base de datos creada correctamente.' AS mensaje;
