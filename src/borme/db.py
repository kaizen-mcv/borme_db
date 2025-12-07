"""Conexion a base de datos PostgreSQL con SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import settings

# Engine de SQLAlchemy
engine = create_engine(settings.db_url, echo=False)

# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Session:
    """Obtener una sesion de base de datos."""
    return SessionLocal()


def init_db():
    """Crear todas las tablas en la base de datos."""
    from .models import Base
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Eliminar todas las tablas de la base de datos."""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
