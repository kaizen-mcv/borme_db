# borme_db

Base de datos PostgreSQL con los datos del Boletín Oficial del Registro
Mercantil (BORME): todos los actos mercantiles de empresas españolas desde
2009. Incluye CLI para descarga incremental y parseo.

**Stack:** Python 3.11+, PostgreSQL, psycopg 3, BOE Datos Abiertos.

## Qué es el BORME

El BORME es la publicación oficial donde se registran todos los actos mercantiles de las empresas españolas:
- Constituciones y disoluciones de empresas
- Nombramientos y ceses de cargos
- Cambios de domicilio, denominación social
- Ampliaciones y reducciones de capital
- Fusiones, escisiones, transformaciones

## Características

- Descarga automática de PDFs desde la API de datos abiertos del BOE
- Parseo de PDFs del BORME a estructuras de datos
- Almacenamiento en PostgreSQL con modelos relacionales
- Seguimiento de cargos actuales e históricos de personas y empresas
- CLI intuitiva con output formateado

## Instalación

### 1. Requisitos previos

```bash
# Dependencias del sistema (para compilar lxml)
sudo apt install libxml2-dev libxslt1-dev

# PostgreSQL (usando Docker)
docker-compose -f config/docker-compose.yml up -d
```

### 2. Instalar el proyecto

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -e .
```

### 3. Configuración

Crear archivo `.env` en la raíz del proyecto:

```bash
BORME_DB_URL=postgresql+psycopg://borme_user:password@localhost:5432/borme_db
BORME_DATA_DIR=./data
```

## Uso

### Comandos disponibles

```bash
# Inicializar base de datos (crear tablas)
borme init

# Ver estadísticas de la base de datos
borme status

# Descargar e importar BORME de hoy
borme today

# Descargar rango de fechas
borme download --from 2024-01-01 --to 2024-12-31

# Importar PDF específico
borme pdf BORME-A-2024-123-28.pdf

# Importar JSON específico
borme json BORME-A-2024-123-28.json
```

### Ejemplo de sesión

```bash
$ borme init
Base de datos inicializada correctamente

$ borme download --from 2024-11-25 --to 2024-12-05
Descargando BORMEs desde 2024-11-25 hasta 2024-12-05
DATE: 2024-11-25
  Descargado: BORME-A-2024-227-03.pdf
  ...
BORMEs creados: 274/275
Anuncios creados: 24085
Tiempo total: 154.64s

$ borme status
 Estadisticas BORME
┏━━━━━━━━━━┳━━━━━━━┓
┃ Entidad  ┃ Total ┃
┡━━━━━━━━━━╇━━━━━━━┩
│ BORMEs   │   274 │
│ Empresas │ 22948 │
│ Personas │ 23407 │
│ Anuncios │ 24085 │
└──────────┴───────┘
```

## Estructura del proyecto

```
borme/
├── src/
│   ├── borme/           # CLI principal
│   │   ├── cli.py       # Comandos Typer
│   │   ├── config.py    # Configuración Pydantic
│   │   ├── db.py        # Conexión SQLAlchemy
│   │   ├── models.py    # Modelos de BD
│   │   ├── importer.py  # Lógica de importación
│   │   ├── downloader.py # Descarga de PDFs
│   │   └── paths.py     # Gestión de rutas
│   │
│   └── bormekai/        # Parser de BORME
│       ├── parser.py    # Parser de PDFs
│       ├── borme.py     # Modelos de datos
│       ├── acto.py      # Tipos de actos
│       ├── cargo.py     # Cargos societarios
│       ├── provincia.py # Provincias
│       └── ...
│
├── config/
│   └── docker-compose.yml  # PostgreSQL
├── data/                   # PDFs y JSONs descargados
├── pyproject.toml
└── .env
```

## Base de datos

### Tablas principales

| Tabla | Descripción |
|-------|-------------|
| `bormes` | Boletines publicados (CVE, fecha, provincia) |
| `companies` | Empresas con sus cargos actuales e históricos |
| `persons` | Personas físicas con sus cargos |
| `anuncios` | Anuncios individuales con actos mercantiles |

### Consultas útiles

```sql
-- Empresas creadas en un mes
SELECT name, date_creation FROM companies
WHERE date_creation BETWEEN '2024-11-01' AND '2024-11-30';

-- Personas con más cargos activos
SELECT name, jsonb_array_length(cargos_actuales) as num_cargos
FROM persons
ORDER BY num_cargos DESC LIMIT 10;

-- Anuncios de una empresa
SELECT a.* FROM anuncios a
JOIN companies c ON a.company_slug = c.slug
WHERE c.name ILIKE '%empresa%';
```

## Dependencias

| Paquete | Uso |
|---------|-----|
| bormeparser | Parser de PDFs del BORME |
| typer | Framework CLI |
| rich | Output formateado |
| sqlalchemy | ORM PostgreSQL |
| psycopg | Driver PostgreSQL v3 |
| pydantic-settings | Configuración desde .env |
| requests | Descarga de PDFs |

## Documentación adicional

- [Arquitectura del proyecto](docs/ARQUITECTURA.md)
- [Guía de desarrollo](docs/DESARROLLO.md)
- [Datos disponibles del BORME](.claude/DATOS_BORME.md)

## Licencia

AGPL-3.0
