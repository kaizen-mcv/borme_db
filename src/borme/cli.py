"""CLI de BORME con Typer."""

import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .db import init_db, get_session
from .importer import import_borme_download, from_pdf_file, from_json_file
from .models import Borme, Company, Person, Anuncio
from .state import DownloadState
from .stats import export_all_stats, get_quick_stats

app = typer.Typer(
    name="borme",
    help="CLI para descarga de datos del BORME a PostgreSQL",
    no_args_is_help=True,
)
console = Console()


@app.command()
def init():
    """Inicializar base de datos (crear tablas)."""
    console.print("[bold]Inicializando base de datos...[/bold]")
    try:
        init_db()
        console.print("[green]Base de datos inicializada correctamente.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def download(
    date_from: str = typer.Option(
        ..., "--from", "-f",
        help="Fecha inicio (YYYY-MM-DD o 'init')"
    ),
    date_to: str = typer.Option(
        ..., "--to", "-t",
        help="Fecha fin (YYYY-MM-DD o 'today')"
    ),
    local_only: bool = typer.Option(
        False, "--local-only",
        help="No descargar, solo procesar archivos locales"
    ),
    strict: bool = typer.Option(
        False, "--strict",
        help="Abortar si falta algun archivo"
    ),
):
    """Descargar e importar BORMEs en un rango de fechas."""
    console.print(f"[bold]Descargando BORMEs desde {date_from} hasta {date_to}[/bold]")

    try:
        success = import_borme_download(
            date_from=date_from,
            date_to=date_to,
            local_only=local_only,
            no_missing=strict,
        )
        if success:
            console.print("[green]Descarga completada.[/green]")
        else:
            console.print("[yellow]Descarga completada con errores.[/yellow]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error inesperado: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def today(
    local_only: bool = typer.Option(
        False, "--local-only",
        help="No descargar, solo procesar archivos locales"
    ),
):
    """Descargar e importar BORME del dia de hoy."""
    today_str = datetime.date.today().isoformat()
    console.print(f"[bold]Descargando BORME de hoy ({today_str})[/bold]")

    try:
        success = import_borme_download(
            date_from=today_str,
            date_to=today_str,
            local_only=local_only,
        )
        if success:
            console.print("[green]Descarga completada.[/green]")
        else:
            console.print("[yellow]No hay BORME disponible para hoy.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def pdf(
    files: list[str] = typer.Argument(..., help="Archivos PDF a importar"),
):
    """Importar archivos BORME-PDF."""
    for file in files:
        console.print(f"[bold]Importando {file}...[/bold]")
        success, results = from_pdf_file(file)
        if success:
            console.print(f"  Empresas: {results.get('created_companies', 0)}")
            console.print(f"  Personas: {results.get('created_persons', 0)}")
            console.print(f"  Anuncios: {results.get('created_anuncios', 0)}")


@app.command("json")
def json_cmd(
    files: list[str] = typer.Argument(..., help="Archivos JSON a importar"),
):
    """Importar archivos BORME-JSON."""
    for file in files:
        console.print(f"[bold]Importando {file}...[/bold]")
        success, results = from_json_file(file)
        if success:
            console.print(f"  Empresas: {results.get('created_companies', 0)}")
            console.print(f"  Personas: {results.get('created_persons', 0)}")
            console.print(f"  Anuncios: {results.get('created_anuncios', 0)}")


@app.command()
def status():
    """Mostrar estadisticas de la base de datos."""
    session = get_session()
    try:
        bormes = session.query(Borme).count()
        companies = session.query(Company).count()
        persons = session.query(Person).count()
        anuncios = session.query(Anuncio).count()

        table = Table(title="Estadisticas BORME")
        table.add_column("Entidad", style="cyan")
        table.add_column("Total", style="green", justify="right")

        table.add_row("BORMEs", str(bormes))
        table.add_row("Empresas", str(companies))
        table.add_row("Personas", str(persons))
        table.add_row("Anuncios", str(anuncios))

        console.print(table)
    finally:
        session.close()


@app.command()
def stats(
    reset: bool = typer.Option(
        False, "--reset", "-r",
        help="Reiniciar el estado de descarga"
    ),
):
    """Mostrar estadisticas del estado de descarga."""
    state = DownloadState()

    if reset:
        if typer.confirm("¿Estás seguro de reiniciar el estado?"):
            state.reset()
            console.print("[green]Estado reiniciado.[/green]")
        return

    summary = state.get_summary()

    if not summary["downloaded"] and not summary["failed"]:
        console.print("[yellow]No hay estado de descarga guardado.[/yellow]")
        console.print("Ejecuta 'borme download' para iniciar una descarga.")
        return

    # Tabla de estado
    table = Table(title="Estado de Descarga")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green", justify="right")

    table.add_row("BORMEs descargados", str(summary["downloaded"]))
    table.add_row("BORMEs fallidos", str(summary["failed"]))
    table.add_row("BORMEs saltados", str(summary["skipped"]))
    table.add_row("Empresas creadas", str(summary["companies"]))
    table.add_row("Personas creadas", str(summary["persons"]))
    table.add_row("Anuncios creados", str(summary["anuncios"]))

    if summary.get("elapsed_seconds"):
        hours = summary["elapsed_seconds"] / 3600
        table.add_row("Tiempo total", f"{hours:.2f} horas")

    if summary.get("start_time"):
        table.add_row("Inicio", summary["start_time"][:19].replace("T", " "))

    if summary.get("last_update"):
        table.add_row("Última actualización", summary["last_update"][:19].replace("T", " "))

    console.print(table)

    # Mostrar errores si hay
    if summary.get("errors"):
        console.print("\n[bold red]Errores recientes:[/bold red]")
        for cve, error in summary["errors"].items():
            console.print(f"  [red]{cve}[/red]: {error[:60]}...")


@app.command("export-stats")
def export_stats_cmd():
    """Exportar estadísticas de la base de datos a archivos JSON."""
    console.print("[bold]Generando estadísticas...[/bold]")

    try:
        exported = export_all_stats()

        console.print(f"\n[green]Estadísticas exportadas a .stats/:[/green]")
        for filename, path in exported.items():
            console.print(f"  [dim]{filename}[/dim]")

        # Mostrar resumen rápido
        quick = get_quick_stats()
        console.print("\n[bold]Resumen:[/bold]")

        table = Table()
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green", justify="right")

        table.add_row("BORMEs", f"{quick['totals']['bormes']:,}")
        table.add_row("Empresas", f"{quick['totals']['companies']:,}")
        table.add_row("  - Activas", f"{quick['companies']['active']:,}")
        table.add_row("  - Extinguidas", f"{quick['companies']['extinct']:,}")
        table.add_row("Personas", f"{quick['totals']['persons']:,}")
        table.add_row("Anuncios", f"{quick['totals']['anuncios']:,}")
        table.add_row("Cobertura", f"{quick['coverage']['first_date']} a {quick['coverage']['last_date']}")
        table.add_row("Provincias", str(quick['coverage']['provinces']))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error generando estadísticas: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
