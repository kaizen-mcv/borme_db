"""Logica de importacion de BORME."""

import datetime
import time
from pathlib import Path

import bormekai
from bormekai.regex import is_company, is_acto_cargo_entrante, regex_empresa_tipo
from bormekai.borme import BormeActoCargo
from rich.console import Console
from slugify import slugify

from .config import settings
from .db import get_session
from .logger import get_logger, setup_logging
from .state import DownloadState
from .models import (
    Borme, Company, Person, Anuncio, BormeLog,
    get_or_create_borme, get_or_create_company, get_or_create_person,
    get_or_create_anuncio, get_or_create_bormelog,
)
from .paths import get_borme_pdf_path, get_borme_json_path, files_exist
from .downloader import download_pdfs, get_sumario, _next_business_day

logger = get_logger(__name__)
console = Console()

# Estado global de descarga (se inicializa en import_borme_download)
_download_state: DownloadState = None


def parse_empresa(cve: str, nombre: str) -> tuple[str, str, str]:
    """Parsear nombre de empresa y obtener tipo y slug."""
    empresa, tipo = regex_empresa_tipo(nombre)
    slug_c = slugify(empresa)

    if tipo == "":
        logger.warning(f"[{cve}] Tipo de empresa no detectado: {empresa}")

    return empresa, tipo, slug_c


def slug2(val: str) -> str:
    """Obtener slug de nombre completo de sociedad."""
    empresa, _ = regex_empresa_tipo(val)
    return slugify(empresa)


def extinguir_sociedad(session, company: Company, date: datetime.date):
    """Marcar sociedad como extinguida y cesar todos los cargos."""
    company.is_active = False
    company.date_extinction = date
    company.date_updated = date

    # Cesar cargos de empresas
    for cargo in company.cargos_actuales_c:
        cargo["date_to"] = date.isoformat()
        company.cargos_historial_c = company.cargos_historial_c + [cargo]
        c_cesada = session.get(Company, slug2(cargo["name"]))
        if c_cesada:
            _cesar_cargo_company(c_cesada, company.fullname, date.isoformat())

    # Cesar cargos de personas
    for cargo in company.cargos_actuales_p:
        cargo["date_to"] = date.isoformat()
        company.cargos_historial_p = company.cargos_historial_p + [cargo]
        p_cesada = session.get(Person, slug2(cargo["name"]))
        if p_cesada:
            _cesar_cargo_person(p_cesada, company.fullname, date.isoformat())

    company.cargos_actuales_c = []
    company.cargos_actuales_p = []


def _cesar_cargo_company(company: Company, company_name: str, date: str):
    """Cesar cargo de una empresa."""
    for cargo in company.cargos_actuales_c:
        if cargo["name"] == company_name:
            new_list = [c for c in company.cargos_actuales_c if c != cargo]
            company.cargos_actuales_c = new_list
            cargo["date_to"] = date
            company.cargos_historial_c = company.cargos_historial_c + [cargo]
            break


def _cesar_cargo_person(person: Person, company_name: str, date: str):
    """Cesar cargo de una persona."""
    for cargo in person.cargos_actuales:
        if cargo["name"] == company_name:
            new_list = [c for c in person.cargos_actuales if c != cargo]
            person.cargos_actuales = new_list
            cargo["date_to"] = date
            person.cargos_historial = person.cargos_historial + [cargo]
            break


def _from_instance(session, borme) -> dict:
    """Importar en la BD una instancia bormekai.Borme."""
    logger.info(f"\nBORME CVE: {borme.cve} ({borme.date}, {borme.provincia}, [{borme.anuncios_rango[0]}-{borme.anuncios_rango[1]}])")

    results = {
        "created_anuncios": 0,
        "created_bormes": 0,
        "created_companies": 0,
        "created_persons": 0,
        "total_anuncios": 0,
        "total_bormes": 0,
        "total_companies": 0,
        "total_persons": 0,
        "errors": 0
    }

    # Create borme
    nuevo_borme, created = get_or_create_borme(session, borme)
    if created:
        logger.debug(f"Creado BORME: {borme.cve}")
        results["created_bormes"] += 1

    # Create bormelog
    borme_log, _ = get_or_create_bormelog(session, nuevo_borme, borme.filename)
    if borme_log.parsed:
        logger.warning(f"{borme.cve} ya ha sido analizado.")
        return results

    borme_embed = {"cve": nuevo_borme.cve, "url": nuevo_borme.url}

    for n, anuncio in enumerate(borme.get_anuncios(), 1):
        try:
            logger.debug(f"{n}: Importando anuncio: {anuncio}")
            results["total_companies"] += 1

            # Create empresa
            empresa, tipo, slug_c = parse_empresa(borme.cve, anuncio.empresa)
            company, created = get_or_create_company(session, empresa, tipo, slug_c, borme.date)

            if created:
                logger.debug(f"Creada empresa: {empresa} ({tipo})")
                results["created_companies"] += 1
            else:
                if company.name != empresa:
                    logger.debug(f"Empresa similar: {company.name} vs {empresa}")
                results["errors"] += 1

            company.add_in_bormes(borme_embed)
            company.anuncios = company.anuncios + [{"year": borme.date.year, "id": anuncio.id}]
            company.date_updated = borme.date

            # Create anuncio
            nuevo_anuncio, created = get_or_create_anuncio(session, anuncio, borme.date.year, nuevo_borme, company.slug)
            if created:
                logger.debug(f"Creado anuncio: {anuncio.id} - {empresa} ({tipo})")
                results["created_anuncios"] += 1

            for acto in anuncio.get_borme_actos():
                logger.debug(f"Acto: {acto.name}")

                if isinstance(acto, BormeActoCargo):
                    lista_cargos = []
                    for nombre_cargo, nombres in acto.cargos.items():
                        logger.debug(f"Cargo: {nombre_cargo} ({len(nombres)})")
                        for nombre in nombres:
                            logger.debug(f"  {nombre}")
                            if is_company(nombre):
                                results["total_companies"] += 1
                                cargo, c_created = _load_cargo_empresa(
                                    session, nombre, borme, anuncio,
                                    borme_embed, nombre_cargo, acto, company
                                )
                                if c_created:
                                    results["created_companies"] += 1
                                else:
                                    results["errors"] += 1
                            else:
                                results["total_persons"] += 1
                                cargo, p_created = _load_cargo_person(
                                    session, nombre, borme, company,
                                    borme_embed, nombre_cargo, acto
                                )
                                if p_created:
                                    results["created_persons"] += 1
                                else:
                                    results["errors"] += 1
                            lista_cargos.append(cargo)

                    nuevo_anuncio.actos = {**nuevo_anuncio.actos, acto.name: lista_cargos}

                    if is_acto_cargo_entrante(acto.name):
                        company.update_cargos_entrantes(lista_cargos)
                    else:
                        company.update_cargos_salientes(lista_cargos)
                else:
                    nuevo_anuncio.actos = {**nuevo_anuncio.actos, acto.name: acto.value}

                    if acto.name == "Extinción":
                        extinguir_sociedad(session, company, borme.date)

            nuevo_borme.anuncios = nuevo_borme.anuncios + [{"year": borme.date.year, "id": anuncio.id}]

        except Exception as e:
            logger.error(f"[{borme.cve}] ERROR importing anuncio {anuncio.id}")
            logger.error(f"[X] {e.__class__.__name__}: {e}")
            session.rollback()
            results["errors"] += 1

    borme_log.errors = results["errors"]
    borme_log.parsed = True
    borme_log.date_parsed = datetime.datetime.now()

    session.commit()
    return results


def _load_cargo_empresa(session, nombre, borme, anuncio, borme_embed, nombre_cargo, acto, company):
    """Importar empresa que aparece en un cargo."""
    empresa, tipo, slug_c = parse_empresa(borme.cve, nombre)
    c, created = get_or_create_company(session, empresa, tipo, slug_c, borme.date)

    if created:
        logger.debug(f"Creada empresa: {empresa} ({tipo})")
    else:
        if c.name != empresa:
            logger.debug(f"Empresa similar: {c.name} vs {empresa}")

    c.anuncios = c.anuncios + [{"year": borme.date.year, "id": anuncio.id}]
    c.add_in_bormes(borme_embed)
    c.date_updated = borme.date

    cargo = {
        "title": nombre_cargo,
        "name": c.fullname,
        "type": "company"
    }

    cargo_embed = {
        "title": nombre_cargo,
        "name": company.fullname,
        "type": "company"
    }

    if is_acto_cargo_entrante(acto.name):
        cargo["date_from"] = borme.date.isoformat()
        cargo_embed["date_from"] = borme.date.isoformat()
        c.update_cargos_entrantes([cargo_embed])
    else:
        cargo["date_to"] = borme.date.isoformat()
        cargo_embed["date_to"] = borme.date.isoformat()
        c.update_cargos_salientes([cargo_embed])

    return cargo, created


def _load_cargo_person(session, nombre, borme, company, borme_embed, nombre_cargo, acto):
    """Importar persona que aparece en un cargo."""
    p, created = get_or_create_person(session, nombre, borme.date)

    if created:
        logger.debug(f"Creada persona: {nombre}")
    else:
        if p.name != nombre:
            logger.debug(f"Persona similar: {p.name} vs {nombre}")

    p.add_in_companies(company.fullname)
    p.add_in_bormes(borme_embed)
    p.date_updated = borme.date

    cargo = {
        "title": nombre_cargo,
        "name": p.name,
        "type": "person"
    }

    cargo_embed = {
        "title": nombre_cargo,
        "name": company.fullname,
    }

    if is_acto_cargo_entrante(acto.name):
        cargo["date_from"] = borme.date.isoformat()
        cargo_embed["date_from"] = borme.date.isoformat()
        p.update_cargos_entrantes([cargo_embed])
    else:
        cargo["date_to"] = borme.date.isoformat()
        cargo_embed["date_to"] = borme.date.isoformat()
        p.update_cargos_salientes([cargo_embed])

    return cargo, created


def import_borme_download(
    date_from: str,
    date_to: str,
    seccion=bormekai.SECCION.A,
    local_only: bool = False,
    no_missing: bool = False,
    resume: bool = True,
) -> bool:
    """Descargar e importar BORMEs.

    Args:
        date_from: Fecha inicio (YYYY-MM-DD o "init")
        date_to: Fecha fin (YYYY-MM-DD o "today")
        seccion: Sección del BORME
        local_only: Solo procesar archivos locales
        no_missing: Fallar si hay errores
        resume: Reanudar descarga anterior si existe estado
    """
    global _download_state

    # Inicializar logging
    log_path = setup_logging(log_level="INFO", console=False)
    logger.info(f"Log guardado en: {log_path}")
    console.print(f"[dim]Log: {log_path}[/dim]")

    # Inicializar estado de descarga
    _download_state = DownloadState()

    if _download_state.downloaded_cves and resume:
        console.print(
            f"[green]Estado cargado: {len(_download_state.downloaded_cves)} BORMEs descargados, "
            f"{len(_download_state.failed_cves)} fallidos[/green]"
        )
    else:
        _download_state.reset()

    _download_state.start_download()

    # Primer BORME digital disponible
    FIRST_DIGITAL_BORME = datetime.date(2009, 1, 2)

    if date_from == "init":
        date_from_dt = FIRST_DIGITAL_BORME
    else:
        parts = tuple(map(int, date_from.split("-")))
        date_from_dt = datetime.date(*parts)

    if date_to == "today":
        date_to_dt = datetime.date.today()
    else:
        parts = tuple(map(int, date_to.split("-")))
        date_to_dt = datetime.date(*parts)

    # Validar fecha mínima
    if date_from_dt < FIRST_DIGITAL_BORME:
        console.print(
            f"[yellow]El BORME digital comenzó el {FIRST_DIGITAL_BORME}. "
            f"Ajustando fecha de inicio.[/yellow]"
        )
        logger.warning(f"Fecha ajustada de {date_from_dt} a {FIRST_DIGITAL_BORME}")
        date_from_dt = FIRST_DIGITAL_BORME

    if date_from_dt > date_to_dt:
        raise ValueError("date_from > date_to")

    ret, _ = _import_borme_download_range(
        date_from_dt, date_to_dt, seccion, local_only, strict=no_missing
    )

    # Guardar estado final y mostrar resumen
    _download_state.save()
    _print_state_summary()

    return ret


def _print_state_summary():
    """Imprimir resumen del estado de descarga."""
    if _download_state is None:
        return

    summary = _download_state.get_summary()
    console.print("\n" + "=" * 60)
    console.print("[bold]RESUMEN DE DESCARGA[/bold]")
    console.print("=" * 60)
    console.print(f"BORMEs descargados: {summary['downloaded']}")
    console.print(f"BORMEs fallidos:    {summary['failed']}")
    console.print(f"BORMEs saltados:    {summary['skipped']}")
    console.print(f"Empresas:           {summary['companies']}")
    console.print(f"Personas:           {summary['persons']}")
    console.print(f"Anuncios:           {summary['anuncios']}")

    if summary.get('elapsed_seconds'):
        hours = summary['elapsed_seconds'] / 3600
        console.print(f"Tiempo total:       {hours:.2f} horas")

    if summary.get('errors'):
        console.print("\n[red]Errores recientes:[/red]")
        for cve, error in summary['errors'].items():
            console.print(f"  {cve}: {error[:50]}...")

    console.print("=" * 60)


def _import_borme_download_range(begin, end, seccion, local_only, strict=False, create_json=True):
    """Importar BORMEs en un rango de fechas."""
    global _download_state

    next_date = begin
    total_results = {
        "created_anuncios": 0,
        "created_bormes": 0,
        "created_companies": 0,
        "created_persons": 0,
        "total_anuncios": 0,
        "total_bormes": 0,
        "total_companies": 0,
        "total_persons": 0,
        "errors": 0
    }
    total_start_time = time.time()
    save_interval = 10  # Guardar estado cada N BORMEs
    bormes_processed = 0

    try:
        while next_date and next_date <= end:
            json_path = get_borme_json_path(next_date)
            pdf_path = get_borme_pdf_path(next_date)

            console.print(f"\n[bold]DATE:[/bold] {next_date}")
            logger.info(f"Procesando fecha: {next_date}")

            bormes = []
            if not local_only:
                # Usar nuevo descargador
                pdf_files = download_pdfs(next_date, pdf_path)

                if not pdf_files:
                    console.print(f"[yellow]No hay BORME para {next_date}[/yellow]")
                    logger.info(f"No hay BORME para {next_date}")
                    next_date = _next_business_day(next_date)
                    continue

                for filepath in pdf_files:
                    if str(filepath).endswith("-99.pdf"):
                        continue

                    # Extraer CVE del nombre del archivo
                    cve = Path(filepath).stem

                    # Verificar si ya fue descargado
                    if _download_state and _download_state.is_downloaded(cve):
                        console.print(f"[dim][{cve}] Ya procesado, saltando...[/dim]")
                        _download_state.mark_skipped(cve)
                        continue

                    logger.info(f"Parseando: {filepath}")
                    total_results["total_bormes"] += 1
                    try:
                        bormes.append(bormekai.parse(str(filepath), seccion))
                    except Exception as e:
                        logger.error(f"Error en bormekai.parse(): {filepath}")
                        logger.error(f"{e.__class__.__name__}: {e}")
                        if _download_state:
                            _download_state.mark_failed(cve, str(e))
                        if strict:
                            return False, total_results
            else:
                # Modo local: buscar JSONs o PDFs existentes
                json_files = list(json_path.glob("BORME-A-*.json")) if json_path.exists() else []
                pdf_files = list(pdf_path.glob("BORME-A-*.pdf")) if pdf_path.exists() else []

                if json_files:
                    for f in json_files:
                        cve = f.stem
                        if _download_state and _download_state.is_downloaded(cve):
                            _download_state.mark_skipped(cve)
                            continue
                        bormes.append(bormekai.Borme.from_json(str(f)))
                    total_results["total_bormes"] += len(json_files)
                elif pdf_files:
                    for f in pdf_files:
                        cve = f.stem
                        if _download_state and _download_state.is_downloaded(cve):
                            _download_state.mark_skipped(cve)
                            continue
                        try:
                            bormes.append(bormekai.parse(str(f), seccion))
                        except Exception as e:
                            logger.error(f"Error parseando {f}: {e}")
                            if _download_state:
                                _download_state.mark_failed(cve, str(e))
                    total_results["total_bormes"] += len(pdf_files)
                else:
                    console.print(f"[yellow]No hay archivos locales para {next_date}[/yellow]")

            for borme in sorted(bormes):
                total_results["total_anuncios"] += len(borme.get_anuncios())
                start_time = time.time()

                # Usar sesión independiente por BORME para aislar errores
                borme_session = get_session()
                try:
                    results = _from_instance(borme_session, borme)

                    if create_json:
                        json_path.mkdir(parents=True, exist_ok=True)
                        json_filepath = json_path / f"{borme.cve}.json"
                        borme.to_json(str(json_filepath), include_url=False)

                    for key in total_results.keys():
                        total_results[key] += results.get(key, 0)

                    elapsed_time = time.time() - start_time
                    console.print(f"[dim][{borme.cve}] Tiempo: {elapsed_time:.2f}s[/dim]")
                    logger.info(f"[{borme.cve}] OK ({elapsed_time:.2f}s)")

                    # Actualizar estado
                    if _download_state:
                        _download_state.mark_downloaded(
                            borme.cve,
                            companies=results.get("created_companies", 0),
                            persons=results.get("created_persons", 0),
                            anuncios=results.get("created_anuncios", 0),
                        )
                        bormes_processed += 1

                        # Guardar estado periódicamente
                        if bormes_processed % save_interval == 0:
                            _download_state.save()
                            logger.info(f"Estado guardado ({bormes_processed} BORMEs procesados)")

                except Exception as e:
                    logger.error(f"[{borme.cve}] Error en _from_instance: {e}")
                    borme_session.rollback()

                    if _download_state:
                        _download_state.mark_failed(borme.cve, str(e))

                    if strict:
                        borme_session.close()
                        return False, total_results
                finally:
                    borme_session.close()

            next_date = _next_business_day(next_date)

    except KeyboardInterrupt:
        console.print("\n[yellow]Importacion abortada. Guardando estado...[/yellow]")
        logger.warning("Importacion abortada por el usuario")
        if _download_state:
            _download_state.save()

    return True, total_results


def from_pdf_file(filename: str, create_json: bool = True) -> tuple[bool, dict]:
    """Importar archivo BORME-PDF."""
    results = {
        "created_anuncios": 0,
        "created_bormes": 0,
        "created_companies": 0,
        "created_persons": 0,
        "errors": 0
    }

    session = get_session()
    try:
        borme = bormekai.parse(filename, bormekai.SECCION.A)
        results = _from_instance(session, borme)
        if create_json:
            json_path = get_borme_json_path(borme.date)
            json_path.mkdir(parents=True, exist_ok=True)
            json_filepath = json_path / f"{borme.cve}.json"
            borme.to_json(str(json_filepath))
    except Exception as e:
        logger.error(f"[X] Error en bormekai.parse(): {filename}")
        logger.error(f"[X] {e.__class__.__name__}: {e}")
    finally:
        session.close()

    return True, results


def from_json_file(filename: str) -> tuple[bool, dict]:
    """Importar archivo BORME-JSON."""
    results = {
        "created_anuncios": 0,
        "created_bormes": 0,
        "created_companies": 0,
        "created_persons": 0,
        "errors": 0
    }

    session = get_session()
    try:
        borme = bormekai.Borme.from_json(filename)
        results = _from_instance(session, borme)
    except Exception as e:
        logger.error(f"[X] Error en Borme.from_json(): {filename}")
        logger.error(f"[X] {e.__class__.__name__}: {e}")
    finally:
        session.close()

    return True, results
