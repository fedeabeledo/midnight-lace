from datetime import date, datetime, time

from sqlalchemy import Date, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subasta(Base):
    __tablename__ = "subastas"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(250), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=True)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    estado: Mapped[str | None] = mapped_column(String(10), nullable=True)
    subastador: Mapped[int | None] = mapped_column(Integer, ForeignKey("subastadores.identificador"), nullable=True)
    ubicacion: Mapped[str | None] = mapped_column(String(350), nullable=True)
    capacidad_asistentes: Mapped[int | None] = mapped_column("capacidadAsistentes", Integer, nullable=True)
    tiene_deposito: Mapped[str | None] = mapped_column("tieneDeposito", String(2), nullable=True)
    seguridad_propia: Mapped[str | None] = mapped_column("seguridadPropia", String(2), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(10), nullable=True)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False)
    duracion_item_minutos: Mapped[int] = mapped_column("duracionItemMinutos", Integer, nullable=False)
