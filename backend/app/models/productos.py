from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Producto(Base):
    __tablename__ = "productos"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[date | None] = mapped_column(Date, nullable=True)
    disponible: Mapped[str | None] = mapped_column(String(2), nullable=True)
    descripcion_catalogo: Mapped[str | None] = mapped_column(
        "descripcionCatalogo", String(500), nullable=True, default="No Posee"
    )
    descripcion_completa: Mapped[str] = mapped_column("descripcionCompleta", String(300), nullable=False)
    precio_base: Mapped[Decimal] = mapped_column("precioBase", Numeric(18, 2), nullable=False)
    revisor: Mapped[int] = mapped_column(Integer, ForeignKey("empleados.identificador"), nullable=False)
    duenio: Mapped[int] = mapped_column(Integer, ForeignKey("duenios.identificador"), nullable=False)
    seguro: Mapped[str | None] = mapped_column(String(30), ForeignKey("seguros.nroPoliza"), nullable=True)
    declaracion_propiedad: Mapped[bool] = mapped_column(
        "declaracionPropiedad", Boolean, nullable=False, default=False
    )
    fecha_ingreso: Mapped[date] = mapped_column("fechaIngreso", Date, nullable=False, default=date.today)
    estado_producto: Mapped[str] = mapped_column(
        "estadoProducto", String(15), nullable=False, default="pendiente"
    )
    subastador_asignado: Mapped[int | None] = mapped_column(
        "subastadorAsignado", Integer, ForeignKey("subastadores.identificador"), nullable=True
    )
    deposito: Mapped[int | None] = mapped_column(Integer, ForeignKey("depositos.identificador"), nullable=True)


class Foto(Base):
    __tablename__ = "fotos"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto: Mapped[int] = mapped_column(Integer, ForeignKey("productos.identificador"), nullable=False)
    foto: Mapped[str] = mapped_column(String(500), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DetalleArtistico(Base):
    __tablename__ = "detalleArtistico"

    producto: Mapped[int] = mapped_column(Integer, ForeignKey("productos.identificador"), primary_key=True)
    artista: Mapped[str] = mapped_column(String(200), nullable=False)
    fecha_obra: Mapped[date | None] = mapped_column("fechaObra", Date, nullable=True)
    historia: Mapped[str | None] = mapped_column(Text, nullable=True)


class ComponenteProducto(Base):
    __tablename__ = "componentesProducto"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    producto: Mapped[int] = mapped_column(Integer, ForeignKey("productos.identificador"), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(250), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
