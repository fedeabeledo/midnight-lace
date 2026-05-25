from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CuentaCobro(Base):
    __tablename__ = "cuentasCobro"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    duenio: Mapped[int] = mapped_column(Integer, ForeignKey("duenios.identificador"), nullable=False)
    nombre_banco: Mapped[str] = mapped_column("nombreBanco", String(150), nullable=False)
    numero_cuenta: Mapped[str] = mapped_column("numeroCuenta", String(50), nullable=False)
    pais: Mapped[int | None] = mapped_column(Integer, ForeignKey("paises.numero"), nullable=True)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False)
    activa: Mapped[str] = mapped_column(String(2), nullable=False, default="si")
