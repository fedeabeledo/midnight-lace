from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Asistente(Base):
    __tablename__ = "asistentes"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_postor: Mapped[int] = mapped_column("numeroPostor", Integer, nullable=False)
    cliente: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.identificador"), nullable=False)
    subasta: Mapped[int] = mapped_column(Integer, ForeignKey("subastas.identificador"), nullable=False)


class Pujo(Base):
    __tablename__ = "pujos"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asistente: Mapped[int] = mapped_column(Integer, ForeignKey("asistentes.identificador"), nullable=False)
    item: Mapped[int] = mapped_column(Integer, ForeignKey("itemsCatalogo.identificador"), nullable=False)
    importe: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    ganador: Mapped[str | None] = mapped_column(String(2), nullable=True, default="no")
    realizada_en: Mapped[datetime] = mapped_column("realizadaEn", DateTime(timezone=True), nullable=False, default=datetime.utcnow)
