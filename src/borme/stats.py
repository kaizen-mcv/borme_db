"""Generador de estadísticas del BORME."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from .config import settings
from .db import get_session
from .models import Borme, Company, Person, Anuncio


def get_stats_dir() -> Path:
    """Obtener y crear directorio de estadísticas."""
    stats_dir = settings.stats_dir
    stats_dir.mkdir(parents=True, exist_ok=True)
    return stats_dir


def save_stats(filename: str, data: dict) -> Path:
    """Guardar estadísticas en archivo JSON."""
    stats_dir = get_stats_dir()
    filepath = stats_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    return filepath


# =============================================================================
# ESTADÍSTICAS GENERALES
# =============================================================================

def generate_general_stats(session: Session) -> dict:
    """Generar estadísticas generales de la base de datos."""

    # Conteos básicos
    total_bormes = session.query(Borme).count()
    total_companies = session.query(Company).count()
    total_persons = session.query(Person).count()
    total_anuncios = session.query(Anuncio).count()

    # Empresas activas vs extinguidas
    companies_active = session.query(Company).filter(Company.is_active == True).count()
    companies_extinct = session.query(Company).filter(Company.is_active == False).count()

    # Rango de fechas
    first_borme = session.query(func.min(Borme.date)).scalar()
    last_borme = session.query(func.max(Borme.date)).scalar()

    # Provincias únicas
    provinces = session.query(Borme.province).distinct().count()

    return {
        "generated_at": datetime.now().isoformat(),
        "totals": {
            "bormes": total_bormes,
            "companies": total_companies,
            "persons": total_persons,
            "anuncios": total_anuncios,
        },
        "companies": {
            "active": companies_active,
            "extinct": companies_extinct,
            "extinction_rate": round(companies_extinct / total_companies * 100, 2) if total_companies > 0 else 0,
        },
        "coverage": {
            "first_date": first_borme,
            "last_date": last_borme,
            "provinces": provinces,
        },
    }


# =============================================================================
# ESTADÍSTICAS POR TIEMPO
# =============================================================================

def generate_stats_by_year(session: Session) -> dict:
    """Generar estadísticas agrupadas por año."""

    # BORMEs por año
    bormes_by_year = session.query(
        extract('year', Borme.date).label('year'),
        func.count(Borme.cve).label('count')
    ).group_by('year').order_by('year').all()

    # Anuncios por año
    anuncios_by_year = session.query(
        Anuncio.year,
        func.count(Anuncio.id).label('count')
    ).group_by(Anuncio.year).order_by(Anuncio.year).all()

    return {
        "generated_at": datetime.now().isoformat(),
        "bormes_by_year": {int(row.year): row.count for row in bormes_by_year},
        "anuncios_by_year": {row.year: row.count for row in anuncios_by_year},
    }


def generate_stats_by_month(session: Session, year: int = None) -> dict:
    """Generar estadísticas agrupadas por mes."""

    query = session.query(
        extract('year', Borme.date).label('year'),
        extract('month', Borme.date).label('month'),
        func.count(Borme.cve).label('count')
    )

    if year:
        query = query.filter(extract('year', Borme.date) == year)

    results = query.group_by('year', 'month').order_by('year', 'month').all()

    data = {}
    for row in results:
        year_key = int(row.year)
        if year_key not in data:
            data[year_key] = {}
        data[year_key][int(row.month)] = row.count

    return {
        "generated_at": datetime.now().isoformat(),
        "bormes_by_month": data,
    }


# =============================================================================
# ESTADÍSTICAS POR TIPO DE EMPRESA
# =============================================================================

def generate_stats_by_company_type(session: Session) -> dict:
    """Generar estadísticas por tipo de empresa."""

    # Distribución por tipo
    by_type = session.query(
        Company.type,
        func.count(Company.slug).label('count')
    ).group_by(Company.type).order_by(func.count(Company.slug).desc()).all()

    # Activas vs extinguidas por tipo
    by_type_status = session.query(
        Company.type,
        Company.is_active,
        func.count(Company.slug).label('count')
    ).group_by(Company.type, Company.is_active).all()

    status_data = {}
    for row in by_type_status:
        if row.type not in status_data:
            status_data[row.type] = {"active": 0, "extinct": 0}
        if row.is_active:
            status_data[row.type]["active"] = row.count
        else:
            status_data[row.type]["extinct"] = row.count

    return {
        "generated_at": datetime.now().isoformat(),
        "distribution": {row.type: row.count for row in by_type},
        "by_status": status_data,
    }


# =============================================================================
# ESTADÍSTICAS POR PROVINCIA
# =============================================================================

def generate_stats_by_province(session: Session) -> dict:
    """Generar estadísticas por provincia."""

    # BORMEs por provincia
    bormes_by_province = session.query(
        Borme.province,
        func.count(Borme.cve).label('count')
    ).group_by(Borme.province).order_by(func.count(Borme.cve).desc()).all()

    # Anuncios por provincia (a través de BORME)
    anuncios_by_province = session.query(
        Borme.province,
        func.count(Anuncio.id).label('count')
    ).join(Anuncio, Anuncio.borme_cve == Borme.cve
    ).group_by(Borme.province).order_by(func.count(Anuncio.id).desc()).all()

    return {
        "generated_at": datetime.now().isoformat(),
        "bormes_by_province": {row.province: row.count for row in bormes_by_province},
        "anuncios_by_province": {row.province: row.count for row in anuncios_by_province},
    }


# =============================================================================
# RANKINGS
# =============================================================================

def generate_rankings(session: Session, limit: int = 100) -> dict:
    """Generar rankings de personas y empresas."""

    # Personas con más cargos actuales (usando JSONB)
    # Nota: esto es aproximado, cuenta el tamaño del array JSONB
    persons_most_positions = session.query(
        Person.name,
        Person.slug,
        func.jsonb_array_length(Person.cargos_actuales).label('num_cargos')
    ).order_by(func.jsonb_array_length(Person.cargos_actuales).desc()
    ).limit(limit).all()

    # Empresas con más anuncios
    companies_most_anuncios = session.query(
        Company.name,
        Company.type,
        Company.slug,
        func.jsonb_array_length(Company.anuncios).label('num_anuncios')
    ).order_by(func.jsonb_array_length(Company.anuncios).desc()
    ).limit(limit).all()

    # Personas en más empresas
    persons_most_companies = session.query(
        Person.name,
        Person.slug,
        func.jsonb_array_length(Person.in_companies).label('num_companies')
    ).order_by(func.jsonb_array_length(Person.in_companies).desc()
    ).limit(limit).all()

    return {
        "generated_at": datetime.now().isoformat(),
        "persons_most_positions": [
            {"name": r.name, "slug": r.slug, "positions": r.num_cargos}
            for r in persons_most_positions if r.num_cargos > 0
        ],
        "companies_most_anuncios": [
            {"name": r.name, "type": r.type, "slug": r.slug, "anuncios": r.num_anuncios}
            for r in companies_most_anuncios if r.num_anuncios > 0
        ],
        "persons_most_companies": [
            {"name": r.name, "slug": r.slug, "companies": r.num_companies}
            for r in persons_most_companies if r.num_companies > 0
        ],
    }


# =============================================================================
# EXPORTAR TODAS LAS ESTADÍSTICAS
# =============================================================================

def export_all_stats() -> dict[str, Path]:
    """Exportar todas las estadísticas a archivos JSON."""

    session = get_session()
    exported = {}

    try:
        # General
        general = generate_general_stats(session)
        exported["general.json"] = save_stats("general.json", general)

        # Por año
        by_year = generate_stats_by_year(session)
        exported["by_year.json"] = save_stats("by_year.json", by_year)

        # Por mes
        by_month = generate_stats_by_month(session)
        exported["by_month.json"] = save_stats("by_month.json", by_month)

        # Por tipo de empresa
        by_type = generate_stats_by_company_type(session)
        exported["by_company_type.json"] = save_stats("by_company_type.json", by_type)

        # Por provincia
        by_province = generate_stats_by_province(session)
        exported["by_province.json"] = save_stats("by_province.json", by_province)

        # Rankings
        rankings = generate_rankings(session)
        exported["rankings.json"] = save_stats("rankings.json", rankings)

    finally:
        session.close()

    return exported


def get_quick_stats() -> dict:
    """Obtener estadísticas rápidas sin guardar a archivo."""
    session = get_session()
    try:
        return generate_general_stats(session)
    finally:
        session.close()
