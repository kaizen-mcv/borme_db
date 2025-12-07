"""Modelos SQLAlchemy para BORME."""

from datetime import date, datetime
from typing import Optional

from slugify import slugify
from sqlalchemy import String, Integer, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base para todos los modelos."""
    pass


class Borme(Base):
    """Edicion de BORME."""

    __tablename__ = "bormes"

    cve: Mapped[str] = mapped_column(String(30), primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    url: Mapped[str] = mapped_column(String(255))
    from_reg: Mapped[int] = mapped_column(Integer)
    until_reg: Mapped[int] = mapped_column(Integer)
    province: Mapped[str] = mapped_column(String(100))
    section: Mapped[str] = mapped_column(String(20))
    anuncios: Mapped[list] = mapped_column(JSONB, default=list)

    # Relaciones
    log: Mapped[Optional["BormeLog"]] = relationship(back_populates="borme")
    anuncio_list: Mapped[list["Anuncio"]] = relationship(back_populates="borme")

    @property
    def total_anuncios(self) -> int:
        return len(self.anuncios)

    def __repr__(self) -> str:
        return self.cve


class Company(Base):
    """Sociedad mercantil."""

    __tablename__ = "companies"

    slug: Mapped[str] = mapped_column(String(260), primary_key=True)
    name: Mapped[str] = mapped_column(String(260), index=True)
    nif: Mapped[str] = mapped_column(String(10), default="")
    type: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_extinction: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_updated: Mapped[date] = mapped_column(Date, index=True)
    in_bormes: Mapped[list] = mapped_column(JSONB, default=list)
    anuncios: Mapped[list] = mapped_column(JSONB, default=list)
    cargos_actuales_p: Mapped[list] = mapped_column(JSONB, default=list)
    cargos_actuales_c: Mapped[list] = mapped_column(JSONB, default=list)
    cargos_historial_p: Mapped[list] = mapped_column(JSONB, default=list)
    cargos_historial_c: Mapped[list] = mapped_column(JSONB, default=list)

    @property
    def fullname(self) -> str:
        return f"{self.name.title()} {self.type}"

    @property
    def total_anuncios(self) -> int:
        return len(self.anuncios)

    @property
    def total_bormes(self) -> int:
        return len(self.in_bormes)

    def add_in_bormes(self, borme: dict):
        """Agregar referencia a BORME si no existe."""
        if borme not in self.in_bormes:
            self.in_bormes = self.in_bormes + [borme]

    def update_cargos_entrantes(self, cargos: list[dict]):
        """Agregar cargos entrantes (nombramientos)."""
        for cargo in cargos:
            cargo_embed = cargo.copy()
            if cargo_embed.get("type") == "company":
                del cargo_embed["type"]
                self.cargos_actuales_c = self.cargos_actuales_c + [cargo_embed]
            elif cargo_embed.get("type") == "person":
                del cargo_embed["type"]
                self.cargos_actuales_p = self.cargos_actuales_p + [cargo_embed]

    def update_cargos_salientes(self, cargos: list[dict]):
        """Procesar cargos salientes (ceses)."""
        for cargo in cargos:
            cargo_embed = cargo.copy()
            if cargo_embed.get("type") == "company":
                del cargo_embed["type"]
                # Buscar en cargos actuales
                for cargo_a in self.cargos_actuales_c:
                    if all(cargo.get(k) == cargo_a.get(k) for k in ("name", "title")):
                        new_list = [c for c in self.cargos_actuales_c if c != cargo_a]
                        self.cargos_actuales_c = new_list
                        cargo_embed["date_from"] = cargo_a.get("date_from")
                        break
                self.cargos_historial_c = self.cargos_historial_c + [cargo_embed]
            elif cargo_embed.get("type") == "person":
                del cargo_embed["type"]
                for cargo_a in self.cargos_actuales_p:
                    if all(cargo.get(k) == cargo_a.get(k) for k in ("name", "title")):
                        new_list = [c for c in self.cargos_actuales_p if c != cargo_a]
                        self.cargos_actuales_p = new_list
                        cargo_embed["date_from"] = cargo_a.get("date_from")
                        break
                self.cargos_historial_p = self.cargos_historial_p + [cargo_embed]

    def __repr__(self) -> str:
        return self.fullname


class Person(Base):
    """Persona fisica."""

    __tablename__ = "persons"

    slug: Mapped[str] = mapped_column(String(200), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    in_companies: Mapped[list] = mapped_column(JSONB, default=list)
    in_bormes: Mapped[list] = mapped_column(JSONB, default=list)
    date_updated: Mapped[date] = mapped_column(Date, index=True)
    cargos_actuales: Mapped[list] = mapped_column(JSONB, default=list)
    cargos_historial: Mapped[list] = mapped_column(JSONB, default=list)

    @property
    def total_companies(self) -> int:
        return len(self.in_companies)

    @property
    def total_bormes(self) -> int:
        return len(self.in_bormes)

    def add_in_companies(self, company: str):
        """Agregar empresa a la lista si no existe."""
        if company not in self.in_companies:
            self.in_companies = self.in_companies + [company]

    def add_in_bormes(self, borme: dict):
        """Agregar referencia a BORME si no existe."""
        if borme not in self.in_bormes:
            self.in_bormes = self.in_bormes + [borme]

    def update_cargos_entrantes(self, cargos: list[dict]):
        """Agregar cargos entrantes."""
        self.cargos_actuales = self.cargos_actuales + cargos

    def update_cargos_salientes(self, cargos: list[dict]):
        """Procesar cargos salientes."""
        for cargo in cargos:
            for cargo_a in self.cargos_actuales:
                if all(cargo.get(k) == cargo_a.get(k) for k in ("name", "title")):
                    new_list = [c for c in self.cargos_actuales if c != cargo_a]
                    self.cargos_actuales = new_list
                    cargo["date_from"] = cargo_a.get("date_from")
                    break
            self.cargos_historial = self.cargos_historial + [cargo]

    def __repr__(self) -> str:
        return self.name


class Anuncio(Base):
    """Anuncio mercantil."""

    __tablename__ = "anuncios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_anuncio: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    borme_cve: Mapped[str] = mapped_column(ForeignKey("bormes.cve"))
    company_slug: Mapped[str] = mapped_column(ForeignKey("companies.slug"))
    datos_registrales: Mapped[str] = mapped_column(String(70))
    actos: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relaciones
    borme: Mapped["Borme"] = relationship(back_populates="anuncio_list")
    company: Mapped["Company"] = relationship()

    __table_args__ = (
        Index("ix_anuncio_id_year", "id_anuncio", "year"),
    )

    @property
    def total_actos(self) -> int:
        return len(self.actos)

    def __repr__(self) -> str:
        return f"{self.id_anuncio} - {self.year} ({self.total_actos} actos)"


class BormeLog(Base):
    """Log de importacion de BORME."""

    __tablename__ = "borme_logs"

    borme_cve: Mapped[str] = mapped_column(
        ForeignKey("bormes.cve"), primary_key=True
    )
    date_created: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    date_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    date_parsed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str] = mapped_column(String(200))

    borme: Mapped["Borme"] = relationship(back_populates="log")

    def __repr__(self) -> str:
        return f"Log({self.borme_cve}): {self.errors} errors"


# Funciones auxiliares para get_or_create

def get_or_create_borme(session, borme_data) -> tuple[Borme, bool]:
    """Obtener o crear un Borme."""
    existing = session.get(Borme, borme_data.cve)
    if existing:
        return existing, False

    # Construir URL sin acceder al servidor (borme_data.url hace llamada HTTP)
    dt = borme_data.date
    url = f"https://www.boe.es/borme/dias/{dt.year}/{dt.month:02d}/{dt.day:02d}/pdfs/{borme_data.cve}.pdf"

    # Manejar provincia como string o enum
    provincia = borme_data.provincia
    if hasattr(provincia, 'name'):
        provincia_name = provincia.name
    else:
        provincia_name = str(provincia)

    borme = Borme(
        cve=borme_data.cve,
        date=borme_data.date,
        url=url,
        from_reg=borme_data.anuncios_rango[0],
        until_reg=borme_data.anuncios_rango[1],
        province=provincia_name,
        section=borme_data.seccion,
        anuncios=[],
    )
    session.add(borme)
    session.flush()
    return borme, True


def get_or_create_company(session, name: str, type_: str, slug_c: str, dt: date = None) -> tuple[Company, bool]:
    """Obtener o crear una Company."""
    existing = session.get(Company, slug_c)
    if existing:
        return existing, False

    company = Company(
        slug=slug_c,
        name=name,
        type=type_,
        date_updated=dt or date.today(),
        in_bormes=[],
        anuncios=[],
        cargos_actuales_p=[],
        cargos_actuales_c=[],
        cargos_historial_p=[],
        cargos_historial_c=[],
    )
    session.add(company)
    session.flush()
    return company, True


def get_or_create_person(session, name: str, dt: date = None) -> tuple[Person, bool]:
    """Obtener o crear una Person."""
    slug_p = slugify(name)
    existing = session.get(Person, slug_p)
    if existing:
        return existing, False

    person = Person(
        slug=slug_p,
        name=name,
        date_updated=dt or date.today(),
        in_companies=[],
        in_bormes=[],
        cargos_actuales=[],
        cargos_historial=[],
    )
    session.add(person)
    session.flush()
    return person, True


def get_or_create_anuncio(session, anuncio_data, year: int, borme: Borme, company_slug: str) -> tuple[Anuncio, bool]:
    """Obtener o crear un Anuncio."""
    existing = session.query(Anuncio).filter_by(
        id_anuncio=anuncio_data.id, year=year
    ).first()
    if existing:
        return existing, False

    anuncio = Anuncio(
        id_anuncio=anuncio_data.id,
        year=year,
        borme_cve=borme.cve,
        company_slug=company_slug,
        datos_registrales=anuncio_data.datos_registrales,
        actos={},
    )
    session.add(anuncio)
    session.flush()
    return anuncio, True


def get_or_create_bormelog(session, borme: Borme, filename: str) -> tuple[BormeLog, bool]:
    """Obtener o crear un BormeLog."""
    existing = session.get(BormeLog, borme.cve)
    if existing:
        return existing, False

    log = BormeLog(
        borme_cve=borme.cve,
        path=filename,
    )
    session.add(log)
    session.flush()
    return log, True
