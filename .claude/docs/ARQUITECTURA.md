# Arquitectura del proyecto BORME

## Visión general

El proyecto BORME es una CLI para descargar y gestionar datos del Boletín Oficial del Registro Mercantil español. Está dividido en dos módulos principales:

```
src/
├── borme/      # CLI y persistencia
└── bormekai/   # Parser de datos BORME
```

## Módulo `borme/` - CLI Principal

### Archivos y responsabilidades

| Archivo | Responsabilidad |
|---------|-----------------|
| `__init__.py` | Paquete principal |
| `__main__.py` | Entry point: `python -m borme` |
| `cli.py` | Comandos Typer (init, download, status, etc.) |
| `config.py` | Configuración Pydantic desde `.env` |
| `db.py` | Conexión SQLAlchemy a PostgreSQL |
| `models.py` | Modelos SQLAlchemy + funciones get_or_create |
| `importer.py` | Lógica de importación de BORMEs |
| `downloader.py` | Descarga de PDFs desde API BOE |
| `paths.py` | Gestión de rutas de archivos |

### Flujo de datos

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (cli.py)                            │
│  borme download --from 2024-01-01 --to 2024-12-31              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Downloader (downloader.py)                   │
│  1. Consulta API BOE: /datosabiertos/api/borme/sumario/YYYYMMDD│
│  2. Descarga PDFs a data/pdf/YYYY/MM/DD/                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Importer (importer.py)                       │
│  1. Parsea PDF con bormekai.parse()                            │
│  2. Guarda JSON cache en data/json/YYYY/MM/DD/                 │
│  3. Crea/actualiza registros en PostgreSQL                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Models (models.py)                           │
│  get_or_create_borme() → Tabla bormes                          │
│  get_or_create_company() → Tabla companies                     │
│  get_or_create_person() → Tabla persons                        │
│  get_or_create_anuncio() → Tabla anuncios                      │
└─────────────────────────────────────────────────────────────────┘
```

## Módulo `bormekai/` - Parser de BORME

Este módulo es un wrapper sobre `bormeparser` (librería externa) que:
- Corrige bugs de bormeparser (provincias bilingües)
- Define modelos de datos propios
- Proporciona interfaz limpia

### Archivos y responsabilidades

| Archivo | Responsabilidad |
|---------|-----------------|
| `__init__.py` | Exporta interfaz pública |
| `parser.py` | Parser de PDFs (usa bormeparser internamente) |
| `borme.py` | Modelos: Borme, BormeAnuncio, BormeActo, BormeActoCargo |
| `acto.py` | Tipos de actos mercantiles (ACTOS_CARGO, etc.) |
| `cargo.py` | Mapa de cargos societarios |
| `provincia.py` | Enum PROVINCIA con 52 provincias |
| `seccion.py` | Enum SECCION (A, B, C) |
| `sociedad.py` | Tipos de sociedades (SL, SA, SLU, etc.) |
| `regex.py` | Funciones regex para parsear empresas |

### Parche de bormeparser

En `parser.py` se parchea `bormeparser.provincia.PROVINCIA.from_title` para soportar nombres bilingües que el BORME usa actualmente:

```python
# Provincias que fallan en bormeparser original:
"ALICANTE/ALACANT" → "ALICANTE"
"CASTELLON/CASTELLO" → "CASTELLON"
"VALENCIA/VALENCIA" → "VALENCIA"
"A CORUÑA" → "A_CORUÑA"
"CIUDAD REAL" → "CIUDAD_REAL"
# ... etc
```

## Modelos de base de datos

### Tabla `bormes`

```sql
CREATE TABLE bormes (
    cve VARCHAR PRIMARY KEY,        -- "BORME-A-2024-227-28"
    date DATE NOT NULL,
    url VARCHAR,
    from_reg INTEGER,
    until_reg INTEGER,
    province VARCHAR,
    section VARCHAR,
    anuncios JSONB                  -- Lista de IDs de anuncios
);
CREATE INDEX ix_bormes_date ON bormes(date);
```

### Tabla `companies`

```sql
CREATE TABLE companies (
    slug VARCHAR PRIMARY KEY,       -- "empresa-ejemplo-sl"
    name VARCHAR NOT NULL,
    nif VARCHAR,
    type VARCHAR,                   -- "SL", "SA", "SLU"
    is_active BOOLEAN DEFAULT true,
    date_creation DATE,
    date_extinction DATE,
    date_updated DATE,
    in_bormes JSONB,               -- ["BORME-A-2024-227-28", ...]
    anuncios JSONB,                -- [1, 2, 3, ...]
    cargos_actuales_p JSONB,       -- Cargos actuales de personas
    cargos_actuales_c JSONB,       -- Cargos actuales de empresas
    cargos_historial_p JSONB,      -- Historial de cargos personas
    cargos_historial_c JSONB       -- Historial de cargos empresas
);
CREATE INDEX ix_companies_name ON companies(name);
CREATE INDEX ix_companies_date_updated ON companies(date_updated);
```

### Tabla `persons`

```sql
CREATE TABLE persons (
    slug VARCHAR PRIMARY KEY,       -- "garcia-lopez-juan"
    name VARCHAR NOT NULL,
    in_companies JSONB,            -- ["empresa-ejemplo-sl", ...]
    in_bormes JSONB,               -- ["BORME-A-2024-227-28", ...]
    date_updated DATE,
    cargos_actuales JSONB,
    cargos_historial JSONB
);
CREATE INDEX ix_persons_name ON persons(name);
CREATE INDEX ix_persons_date_updated ON persons(date_updated);
```

### Tabla `anuncios`

```sql
CREATE TABLE anuncios (
    id SERIAL PRIMARY KEY,
    id_anuncio INTEGER NOT NULL,
    year INTEGER NOT NULL,
    borme_cve VARCHAR REFERENCES bormes(cve),
    company_slug VARCHAR REFERENCES companies(slug),
    datos_registrales VARCHAR,
    actos JSONB                    -- {"Nombramientos": {...}, ...}
);
CREATE INDEX ix_anuncios_id_year ON anuncios(id_anuncio, year);
```

## Configuración

### Variables de entorno

```bash
# Conexión a PostgreSQL
BORME_DB_URL=postgresql+psycopg://user:pass@localhost:5432/borme_db

# Directorio de datos (relativo al proyecto o absoluto)
BORME_DATA_DIR=./data
```

### Estructura de directorios de datos

```
data/
├── pdf/                    # PDFs descargados
│   └── 2024/
│       └── 11/
│           └── 25/
│               ├── BORME-A-2024-227-03.pdf
│               └── ...
├── json/                   # Cache JSON parseado
│   └── 2024/
│       └── 11/
│           └── 25/
│               ├── BORME-A-2024-227-03.json
│               └── ...
└── logs/                   # Logs de ejecución
```

## API del BOE

El proyecto usa la API de datos abiertos del BOE:

```
GET https://www.boe.es/datosabiertos/api/borme/sumario/YYYYMMDD
Accept: application/xml
```

Respuesta XML con enlaces a PDFs de cada provincia.

## Diagrama de clases (bormekai)

```
┌─────────────────────────────────────────────────────────────────┐
│                           Borme                                 │
├─────────────────────────────────────────────────────────────────┤
│ date: date                                                      │
│ seccion: SECCION                                               │
│ provincia: PROVINCIA                                           │
│ num: int                                                       │
│ cve: str                                                       │
│ anuncios: dict[int, BormeAnuncio]                             │
│ filename: str                                                  │
├─────────────────────────────────────────────────────────────────┤
│ to_json() → dict                                               │
│ from_json(data) → Borme                                        │
│ get_anuncios() → list[BormeAnuncio]                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ contiene
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BormeAnuncio                              │
├─────────────────────────────────────────────────────────────────┤
│ id: int                                                        │
│ empresa: str                                                   │
│ registro: str                                                  │
│ sucursal: str                                                  │
│ liquidacion: bool                                              │
│ datos_registrales: str                                         │
│ actos: list[BormeActo]                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ contiene
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BormeActo (abstract)                         │
├─────────────────────────────────────────────────────────────────┤
│                  BormeActoTexto                                 │
│                  (actos con texto libre)                        │
├─────────────────────────────────────────────────────────────────┤
│                  BormeActoCargo                                 │
│                  (nombramientos, ceses, etc.)                   │
│                  value: dict[cargo, set[personas]]              │
└─────────────────────────────────────────────────────────────────┘
```
