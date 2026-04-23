# Guía de desarrollo

## Configuración del entorno

### 1. Clonar y crear entorno virtual

```bash
git clone <repo>
cd borme
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias del sistema

```bash
# Ubuntu/Debian - necesario para compilar lxml
sudo apt install libxml2-dev libxslt1-dev

# También necesitarás PyPDF2 < 3.0 (bormeparser no es compatible con v3)
pip install 'PyPDF2<3.0.0'
```

### 3. Instalar el proyecto en modo desarrollo

```bash
pip install -e .
```

### 4. Levantar PostgreSQL

```bash
docker-compose -f config/docker-compose.yml up -d
```

### 5. Configurar variables de entorno

Crear `.env`:

```bash
BORME_DB_URL=postgresql+psycopg://borme_user:<tu-password>@localhost:5432/borme_db
BORME_DATA_DIR=./data
```

### 6. Inicializar base de datos

```bash
borme init
```

## Dependencias

### Directas (declaradas en pyproject.toml)

| Paquete | Versión | Uso |
|---------|---------|-----|
| bormeparser | >=0.3.1 | Parser de PDFs del BORME |
| typer[all] | >=0.12.0 | Framework CLI |
| rich | >=13.0.0 | Output formateado |
| sqlalchemy | >=2.0.0 | ORM PostgreSQL |
| psycopg[binary] | >=3.1.0 | Driver PostgreSQL v3 |
| pydantic | >=2.5.0 | Validación de datos |
| pydantic-settings | >=2.1.0 | Configuración desde .env |
| python-slugify | >=8.0.0 | Generar slugs URL-friendly |
| requests | >=2.28.0 | HTTP client |

### Indirectas (instaladas automáticamente)

- lxml, pdfminer.six, PyPDF2 (bormeparser)
- click, shellingham (typer)
- markdown-it-py, pygments (rich)
- greenlet, cffi, cryptography (psycopg)
- python-dotenv (pydantic-settings)
- text-unidecode (python-slugify)
- certifi, urllib3, charset-normalizer, idna (requests)

## Problemas conocidos

### 1. bormeparser y provincias bilingües

**Problema**: bormeparser no reconoce nombres de provincias bilingües como "ALICANTE/ALACANT", "VALENCIA/VALENCIA", etc.

**Solución**: En `src/bormekai/parser.py` se parchea `bormeparser.provincia.PROVINCIA.from_title` al importar el módulo.

### 2. bormeparser y PyPDF2 v3

**Problema**: bormeparser usa una API de PyPDF2 que cambió en la versión 3.

**Solución**: Instalar PyPDF2 < 3.0.0:
```bash
pip install 'PyPDF2<3.0.0'
```

### 3. URLs antiguas del BOE

**Problema**: bormeparser intenta descargar de URLs antiguas del BOE que ya no funcionan.

**Solución**: Se creó `src/borme/downloader.py` que usa la nueva API de datos abiertos del BOE.

### 4. Errores de parseo en algunos PDFs

**Problema**: Algunos PDFs tienen formatos no esperados que causan errores en bormeparser.

**Ejemplo**: `AttributeError: 'NoneType' object has no attribute 'groups'`

**Solución actual**: Se captura el error y se continúa con el siguiente PDF. El 99%+ de los PDFs se procesan correctamente.

### 5. Variables de entorno en shell

**Problema**: Si tienes variables `BORME_*` exportadas en tu shell, tienen precedencia sobre el `.env`.

**Solución**:
```bash
unset BORME_DATA_DIR BORME_DB_URL
# o cerrar y abrir la terminal
```

## Estructura del código

```
src/
├── borme/                  # CLI principal
│   ├── __init__.py
│   ├── __main__.py        # python -m borme
│   ├── cli.py             # Comandos: init, download, status, etc.
│   ├── config.py          # Pydantic Settings
│   ├── db.py              # SQLAlchemy engine y session
│   ├── models.py          # Modelos + get_or_create_*
│   ├── importer.py        # from_pdf(), from_json(), from_range()
│   ├── downloader.py      # API BOE + descarga PDFs
│   └── paths.py           # Rutas de archivos
│
└── bormekai/              # Parser de BORME
    ├── __init__.py        # Exporta: parse, Borme, SECCION, PROVINCIA
    ├── parser.py          # parse(filename) → Borme
    ├── borme.py           # Borme, BormeAnuncio, BormeActo*
    ├── acto.py            # ACTO, ACTOS_CARGO, keywords
    ├── cargo.py           # CARGOS dict
    ├── provincia.py       # PROVINCIA enum
    ├── seccion.py         # SECCION enum (A, B, C)
    ├── sociedad.py        # SOCIEDADES, SIGLAS
    └── regex.py           # clean_empresa, is_company, parse_cargos
```

## Comandos útiles

### Desarrollo

```bash
# Probar importación de un PDF
borme pdf data/pdf/2024/11/25/BORME-A-2024-227-28.pdf

# Ver estadísticas
borme status

# Descargar rango pequeño para pruebas
borme download --from 2024-12-01 --to 2024-12-02
```

### Base de datos

```bash
# Conectar a PostgreSQL
psql -h localhost -U borme_user -d borme_db

# Resetear base de datos (eliminar y recrear tablas)
python -c "
from borme.db import engine
from borme.models import Base
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
"
```

### Debug

```bash
# Probar parser directamente
python -c "
import bormekai
borme = bormekai.parse('data/pdf/2024/11/25/BORME-A-2024-227-28.pdf')
print(f'CVE: {borme.cve}')
print(f'Anuncios: {len(borme.anuncios)}')
"

# Ver configuración actual
python -c "
from borme.config import settings
print(f'DB: {settings.db_url}')
print(f'Data: {settings.data_dir}')
"
```

## Añadir nuevas funcionalidades

### Nuevo comando CLI

1. Editar `src/borme/cli.py`
2. Añadir función con decorador `@app.command()`

```python
@app.command()
def mi_comando(argumento: str):
    """Descripción del comando."""
    console.print(f"Argumento: {argumento}")
```

### Nuevo modelo de BD

1. Editar `src/borme/models.py`
2. Añadir clase que herede de `Base`
3. Ejecutar `borme init` para crear la tabla

### Nuevo tipo de acto

1. Editar `src/bormekai/acto.py`
2. Añadir al diccionario `ACTOS` o `ACTOS_CARGO`

## Tests

Actualmente no hay tests automatizados. Para probar manualmente:

```bash
# Test básico de funcionamiento
borme status

# Test de descarga (1 día)
borme download --from 2024-12-01 --to 2024-12-01

# Test de parseo
borme pdf data/pdf/2024/12/01/*.pdf
```
