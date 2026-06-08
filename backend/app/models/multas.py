from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Multa(Base):
    __tablename__ = "multas"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.identificador"), nullable=False)
    registro_subasta: Mapped[int] = mapped_column(
        "registroSubasta", Integer, ForeignKey("registroDeSubasta.identificador"), nullable=False
    )
    importe: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pagada: Mapped[str] = mapped_column(String(2), nullable=False, default="no")
    fecha_emision: Mapped[datetime] = mapped_column(
        "fechaEmision", DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    fecha_vencimiento: Mapped[datetime] = mapped_column("fechaVencimiento", DateTime(timezone=True), nullable=False)
