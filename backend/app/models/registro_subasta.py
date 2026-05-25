from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegistroDeSubasta(Base):
    __tablename__ = "registroDeSubasta"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subasta: Mapped[int] = mapped_column(Integer, ForeignKey("subastas.identificador"), nullable=False)
    duenio: Mapped[int] = mapped_column(Integer, ForeignKey("duenios.identificador"), nullable=False)
    producto: Mapped[int] = mapped_column(Integer, ForeignKey("productos.identificador"), nullable=False)
    cliente: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.identificador"), nullable=False)
    importe: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    comision: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    medio_pago: Mapped[int | None] = mapped_column(
        "medioPago", Integer, ForeignKey("mediosDePago.identificador"), nullable=True
    )
    costo_envio: Mapped[Decimal] = mapped_column("costoEnvio", Numeric(18, 2), nullable=False, default=0)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False)
    retira_personalmente: Mapped[bool] = mapped_column(
        "retiraPersonalmente", Boolean, nullable=False, default=False
    )
    pagado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
