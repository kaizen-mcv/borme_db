# BORME

CLI para descarga de datos del Boletín Oficial del Registro Mercantil (BORME) a PostgreSQL.

## Estructura del proyecto

```
BORME/
├── src/borme/
│   ├── __init__.py
│   ├── __main__.py       # Entry point: python -m borme
│   ├── cli.py            # Comandos Typer
│   ├── config.py         # Configuración Pydantic
│   ├── db.py             # Conexión SQLAlchemy
│   ├── importer.py       # Lógica de descarga
│   ├── models.py         # Modelos: Borme, Company, Person, Anuncio
│   └── paths.py          # Gestión de rutas
├── config/
│   └── docker-compose.yml
├── pyproject.toml
├── .env
└── .venv/
```

## Configuración

Archivo `.env`:
```bash
BORME_DB_URL=postgresql+psycopg://usuario:password@localhost:5432/borme_db
BORME_DATA_DIR=~/.bormes
```

## Comandos CLI

```bash
# Activar entorno virtual
source .venv/bin/activate

# Inicializar base de datos
borme init

# Ver estadísticas
borme status

# Descargar BORME de hoy
borme today

# Descargar rango de fechas
borme download --from 2024-01-01 --to 2024-12-31

# Importar PDF específico
borme pdf archivo.pdf

# Importar JSON específico
borme json archivo.json
```

## Dependencias

```
bormeparser      # Parser de PDFs BORME
sqlalchemy       # ORM
typer            # CLI
rich             # Output formateado
pydantic         # Configuración
psycopg          # PostgreSQL
```

## Datos descargables

Ver `.claude/DATOS_BORME.md` para detalle de:
- Empresas (Company)
- Personas (Person)
- Anuncios mercantiles
- Actos (nombramientos, ceses, etc.)
