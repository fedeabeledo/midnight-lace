from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Catalogo(Base):
    __tablename__ = "catalogos"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descripcion: Mapped[str] = mapped_column(String(250), nullable=False)
    subasta: Mapped[int | None] = mapped_column(Integer, ForeignKey("subastas.identificador"), nullable=True)
    responsable: Mapped[int] = mapped_column(Integer, ForeignKey("empleados.identificador"), nullable=False)


class ItemCatalogo(Base):
    __tablename__ = "itemsCatalogo"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    catalogo: Mapped[int] = mapped_column(Integer, ForeignKey("catalogos.identificador"), nullable=False)
    producto: Mapped[int] = mapped_column(Integer, ForeignKey("productos.identificador"), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    precio_base: Mapped[Decimal] = mapped_column("precioBase", Numeric(18, 2), nullable=False)
    comision: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    subastado: Mapped[str | None] = mapped_column(String(2), nullable=True)
    iniciado_en: Mapped[datetime | None] = mapped_column("iniciadoEn", DateTime(timezone=True), nullable=True)
    finalizado_en: Mapped[datetime | None] = mapped_column("finalizadoEn", DateTime(timezone=True), nullable=True)
