from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MedioDePago(Base):
    __tablename__ = "mediosDePago"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.identificador"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    verificado: Mapped[str] = mapped_column(String(2), nullable=False, default="no")
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, default="ARS")
    activo: Mapped[str] = mapped_column(String(2), nullable=False, default="si")


class CuentaBancaria(Base):
    __tablename__ = "cuentasBancarias"

    medio_pago: Mapped[int] = mapped_column(
        "medioPago", Integer, ForeignKey("mediosDePago.identificador"), primary_key=True
    )
    nombre_banco: Mapped[str] = mapped_column("nombreBanco", String(150), nullable=False)
    numero_cuenta: Mapped[str] = mapped_column("numeroCuenta", String(50), nullable=False)
    pais: Mapped[int | None] = mapped_column(Integer, ForeignKey("paises.numero"), nullable=True)


class TarjetaCredito(Base):
    __tablename__ = "tarjetasDeCredito"

    medio_pago: Mapped[int] = mapped_column(
        "medioPago", Integer, ForeignKey("mediosDePago.identificador"), primary_key=True
    )
    ultimos_cuatro_digitos: Mapped[str] = mapped_column("ultimosCuatroDigitos", String(4), nullable=False)
    nombre_titular: Mapped[str] = mapped_column("nombreTitular", String(150), nullable=False)
    fecha_vencimiento: Mapped[date] = mapped_column("fechaVencimiento", Date, nullable=False)
    red: Mapped[str | None] = mapped_column(String(50), nullable=True)
    es_internacional: Mapped[str] = mapped_column("esInternacional", String(2), nullable=False, default="no")


class ChequeCertificado(Base):
    __tablename__ = "chequesCertificados"

    medio_pago: Mapped[int] = mapped_column(
        "medioPago", Integer, ForeignKey("mediosDePago.identificador"), primary_key=True
    )
    monto_garantizado: Mapped[Decimal] = mapped_column("montoGarantizado", Numeric(18, 2), nullable=False)
    monto_disponible: Mapped[Decimal] = mapped_column("montoDisponible", Numeric(18, 2), nullable=False)
    fecha_entrega: Mapped[date] = mapped_column("fechaEntrega", Date, nullable=False)
    verificado_por: Mapped[int | None] = mapped_column(
        "verificadoPor", Integer, ForeignKey("empleados.identificador"), nullable=True
    )
