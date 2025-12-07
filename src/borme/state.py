"""Gestor de estado para reanudar descargas interrumpidas."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

from .config import settings


class DownloadState:
    """
    Gestor de estado persistente para descargas de BORME.

    Mantiene registro de:
    - CVEs ya descargados
    - CVEs con error
    - Progreso de la descarga
    - Estadísticas
    """

    def __init__(self, state_file: Optional[str] = None):
        """
        Inicializa el gestor de estado.

        Args:
            state_file: Ruta al archivo de estado JSON (None = usar default)
        """
        if state_file is None:
            state_dir = settings.state_dir
            state_dir.mkdir(parents=True, exist_ok=True)
            self.state_file = state_dir / "download_state.json"
        else:
            self.state_file = Path(state_file)
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Estado en memoria
        self.downloaded_cves: Set[str] = set()
        self.failed_cves: Set[str] = set()
        self.errors: Dict[str, str] = {}

        # Estadísticas
        self.stats = {
            "total_downloaded": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "total_companies": 0,
            "total_persons": 0,
            "total_anuncios": 0,
            "start_time": None,
            "last_update": None,
            "last_saved": None,
        }

        # Cargar estado existente si hay
        self.load()

    def load(self) -> bool:
        """
        Carga el estado desde archivo JSON.

        Returns:
            True si se cargó estado existente, False si es nuevo
        """
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Restaurar sets
            self.downloaded_cves = set(data.get("downloaded_cves", []))
            self.failed_cves = set(data.get("failed_cves", []))
            self.errors = data.get("errors", {})

            # Restaurar estadísticas
            saved_stats = data.get("stats", {})
            self.stats.update(saved_stats)

            return True

        except Exception as e:
            print(f"Error cargando estado: {e}")
            return False

    def save(self):
        """Guarda el estado actual a archivo JSON."""
        try:
            # Actualizar timestamp
            self.stats["last_saved"] = datetime.now().isoformat()

            data = {
                "downloaded_cves": list(self.downloaded_cves),
                "failed_cves": list(self.failed_cves),
                "errors": self.errors,
                "stats": self.stats,
            }

            # Guardar a archivo temporal primero (atomic write)
            temp_file = self.state_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Mover archivo temporal al definitivo
            temp_file.replace(self.state_file)

        except Exception as e:
            print(f"Error guardando estado: {e}")

    def mark_downloaded(self, cve: str, companies: int = 0, persons: int = 0, anuncios: int = 0):
        """
        Marca un BORME como descargado exitosamente.

        Args:
            cve: CVE del BORME descargado
            companies: Número de empresas procesadas
            persons: Número de personas procesadas
            anuncios: Número de anuncios procesados
        """
        self.downloaded_cves.add(cve)
        self.stats["total_downloaded"] += 1
        self.stats["total_companies"] += companies
        self.stats["total_persons"] += persons
        self.stats["total_anuncios"] += anuncios
        self.stats["last_update"] = datetime.now().isoformat()

        # Remover de fallidos si estaba
        if cve in self.failed_cves:
            self.failed_cves.remove(cve)
            if cve in self.errors:
                del self.errors[cve]

    def mark_failed(self, cve: str, error: str = ""):
        """
        Marca un BORME como fallido.

        Args:
            cve: CVE del BORME que falló
            error: Mensaje de error
        """
        self.failed_cves.add(cve)
        self.stats["total_failed"] += 1
        self.stats["last_update"] = datetime.now().isoformat()

        if error:
            self.errors[cve] = error

    def mark_skipped(self, cve: str):
        """
        Marca un BORME como saltado (ya existía).

        Args:
            cve: CVE del BORME saltado
        """
        self.stats["total_skipped"] += 1

    def is_downloaded(self, cve: str) -> bool:
        """
        Verifica si un BORME ya fue descargado.

        Args:
            cve: CVE a verificar

        Returns:
            True si ya fue descargado exitosamente
        """
        return cve in self.downloaded_cves

    def is_failed(self, cve: str) -> bool:
        """
        Verifica si un BORME falló previamente.

        Args:
            cve: CVE a verificar

        Returns:
            True si falló en intento previo
        """
        return cve in self.failed_cves

    def get_progress(self, total: Optional[int] = None) -> dict:
        """
        Retorna información de progreso.

        Args:
            total: Total de BORMEs a descargar (opcional)

        Returns:
            Diccionario con información de progreso
        """
        downloaded = len(self.downloaded_cves)
        failed = len(self.failed_cves)
        processed = downloaded + failed

        progress = {
            "downloaded": downloaded,
            "failed": failed,
            "skipped": self.stats["total_skipped"],
            "processed": processed,
            "companies": self.stats["total_companies"],
            "persons": self.stats["total_persons"],
            "anuncios": self.stats["total_anuncios"],
        }

        if total is not None:
            progress["total"] = total
            progress["remaining"] = total - processed
            progress["percent_complete"] = (
                (processed / total * 100) if total > 0 else 0
            )

        # Calcular velocidad
        if self.stats["start_time"]:
            start = datetime.fromisoformat(self.stats["start_time"])
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed > 0:
                progress["bormes_per_second"] = processed / elapsed
                progress["elapsed_seconds"] = elapsed

                if total and processed > 0:
                    estimated_total = (total / processed) * elapsed
                    progress["estimated_remaining_seconds"] = estimated_total - elapsed

        return progress

    def start_download(self):
        """Inicia una sesión de descarga (registra timestamp de inicio)."""
        if not self.stats["start_time"]:
            self.stats["start_time"] = datetime.now().isoformat()

    def reset(self):
        """Reinicia el estado completamente."""
        self.downloaded_cves.clear()
        self.failed_cves.clear()
        self.errors.clear()
        self.stats = {
            "total_downloaded": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "total_companies": 0,
            "total_persons": 0,
            "total_anuncios": 0,
            "start_time": None,
            "last_update": None,
            "last_saved": None,
        }
        self.save()

    def get_summary(self) -> dict:
        """
        Obtiene un resumen del estado actual.

        Returns:
            Diccionario con resumen
        """
        progress = self.get_progress()
        return {
            "downloaded": progress["downloaded"],
            "failed": progress["failed"],
            "skipped": progress["skipped"],
            "companies": progress["companies"],
            "persons": progress["persons"],
            "anuncios": progress["anuncios"],
            "start_time": self.stats["start_time"],
            "last_update": self.stats["last_update"],
            "elapsed_seconds": progress.get("elapsed_seconds"),
            "errors": dict(list(self.errors.items())[:5]),  # Primeros 5 errores
        }
