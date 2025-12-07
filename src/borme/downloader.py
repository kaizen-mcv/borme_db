"""Descargador de BORMEs usando la API de datos abiertos del BOE."""

import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import requests
from rich.console import Console

from .config import settings

console = Console()

BOE_API_URL = "https://www.boe.es/datosabiertos/api/borme/sumario/{date}"


def get_sumario(dt: date) -> dict | None:
    """Obtener sumario del BORME para una fecha."""
    url = BOE_API_URL.format(date=dt.strftime("%Y%m%d"))
    headers = {"Accept": "application/xml"}

    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200:
            return None

        root = ET.fromstring(r.text)
        status = root.find(".//status/code")
        if status is None or status.text != "200":
            return None

        # Extraer PDFs de sección A
        pdfs = []
        for item in root.findall(".//seccion[@codigo='A']/item"):
            identificador = item.find("identificador")
            url_pdf = item.find("url_pdf")
            titulo = item.find("titulo")
            if identificador is not None and url_pdf is not None:
                pdfs.append({
                    "cve": identificador.text,
                    "url": url_pdf.text,
                    "provincia": titulo.text if titulo is not None else ""
                })

        # Obtener fecha del siguiente BORME (si existe)
        # La API no proporciona esto directamente, calculamos el siguiente día hábil
        next_date = _next_business_day(dt)

        return {
            "date": dt,
            "pdfs": pdfs,
            "next_date": next_date
        }
    except Exception as e:
        console.print(f"[red]Error obteniendo sumario: {e}[/red]")
        return None


def _next_business_day(dt: date) -> date:
    """Calcular siguiente día hábil (lun-vie)."""
    next_dt = dt + timedelta(days=1)
    while next_dt.weekday() >= 5:  # 5=sábado, 6=domingo
        next_dt += timedelta(days=1)
    return next_dt


def download_pdfs(dt: date, output_dir: Path = None) -> list[Path]:
    """Descargar todos los PDFs del BORME para una fecha."""
    sumario = get_sumario(dt)
    if not sumario or not sumario["pdfs"]:
        return []

    if output_dir is None:
        year = str(dt.year)
        month = f"{dt.month:02d}"
        day = f"{dt.day:02d}"
        output_dir = settings.pdf_dir / year / month / day

    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for pdf_info in sumario["pdfs"]:
        filename = f"{pdf_info['cve']}.pdf"
        filepath = output_dir / filename

        if filepath.exists():
            console.print(f"[dim]  Ya existe: {filename}[/dim]")
            downloaded.append(filepath)
            continue

        try:
            r = requests.get(pdf_info["url"], timeout=60)
            if r.status_code == 200:
                filepath.write_bytes(r.content)
                console.print(f"[green]  Descargado: {filename}[/green]")
                downloaded.append(filepath)
            else:
                console.print(f"[red]  Error {r.status_code}: {filename}[/red]")
        except Exception as e:
            console.print(f"[red]  Error descargando {filename}: {e}[/red]")

    return downloaded


def download_range(date_from: date, date_to: date) -> dict[date, list[Path]]:
    """Descargar BORMEs en un rango de fechas."""
    results = {}
    current = date_from

    while current <= date_to:
        console.print(f"\n[bold]Fecha: {current}[/bold]")

        pdfs = download_pdfs(current)
        if pdfs:
            results[current] = pdfs
            console.print(f"  [dim]{len(pdfs)} archivos[/dim]")
        else:
            console.print(f"  [yellow]No hay BORME para esta fecha[/yellow]")

        current = _next_business_day(current)

    return results
