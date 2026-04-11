# Inventario PYME — Guía de instalación

## Requisitos
- Python 3.8+
- MySQL 5.7+ o MariaDB
- pip

## Instalación paso a paso

### 1. Instalar dependencias Python

```bash
pip install flask flask-cors mysql-connector-python openpyxl
```

### 2. Crear la base de datos

```bash
mysql -u root -p < setup.sql
```

Esto crea la base de datos `pyme_db`, la tabla `productos` y 5 productos de ejemplo.

### 3. Configurar credenciales MySQL

Abre `app.py` y edita el bloque `DB_CONFIG`:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",        # tu usuario MySQL
    "password": "TU_CLAVE",    # tu contraseña
    "database": "pyme_db"
}
```

### 4. Iniciar el servidor

```bash
python app.py
```

### 5. Abrir la aplicación

Abre tu navegador en: **http://localhost:5000**

---

## Estructura de archivos

```
inventario_pyme/
├── app.py          ← Backend Flask (API REST + servidor web)
├── setup.sql       ← Script para crear la base de datos
├── requirements.txt
└── static/
    └── index.html  ← Interfaz web completa
```

## API REST disponible

| Método | Ruta                    | Descripción                  |
|--------|-------------------------|------------------------------|
| GET    | /api/productos          | Listar todos los productos   |
| GET    | /api/productos?q=texto  | Buscar productos             |
| POST   | /api/productos          | Añadir un producto           |
| PUT    | /api/productos/:id      | Editar un producto           |
| DELETE | /api/productos/:id      | Eliminar un producto         |
| POST   | /api/importar           | Importar archivo Excel       |
| GET    | /api/estadisticas       | Totales y métricas           |

## Formato Excel esperado

| A (Código) | B (Nombre)           | C (Precio) | D (Stock) |
|------------|----------------------|------------|-----------|
| P001       | Cuaderno universitario | 3.50     | 120       |
| P002       | Bolígrafo azul x12   | 5.99       | 45        |

La fila 1 es el encabezado (se ignora). Los datos comienzan en la fila 2.
