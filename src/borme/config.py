"""Configuracion de BORME usando Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directorio raíz del proyecto (donde está pyproject.toml)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Configuracion del CLI BORME."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="BORME_",
    )

    # Base de datos PostgreSQL
    db_url: str = "postgresql+psycopg://borme:borme@localhost:5432/borme_db"

    @property
    def data_dir(self) -> Path:
        """Directorio de datos (siempre dentro del proyecto)."""
        return PROJECT_ROOT / "data"

    @property
    def pdf_dir(self) -> Path:
        """Directorio para PDFs descargados."""
        return self.data_dir / "pdf"

    @property
    def xml_dir(self) -> Path:
        """Directorio para XMLs de indice."""
        return self.data_dir / "xml"

    @property
    def json_dir(self) -> Path:
        """Directorio para cache JSON."""
        return self.data_dir / "json"

    @property
    def log_dir(self) -> Path:
        """Directorio para logs."""
        return self.data_dir / "logs"

    @property
    def state_dir(self) -> Path:
        """Directorio para estado de descarga."""
        return self.data_dir / "state"

    @property
    def stats_dir(self) -> Path:
        """Directorio para estadísticas exportadas (en raíz del proyecto)."""
        return Path(__file__).parent.parent.parent / ".stats"


settings = Settings()
