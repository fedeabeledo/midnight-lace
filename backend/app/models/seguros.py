from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Seguro(Base):
    __tablename__ = "seguros"

    nro_poliza: Mapped[str] = mapped_column("nroPoliza", String(30), primary_key=True)
    compania: Mapped[str] = mapped_column(String(150), nullable=False)
    poliza_combinada: Mapped[str | None] = mapped_column("polizaCombinada", String(2), nullable=True)
    importe: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
