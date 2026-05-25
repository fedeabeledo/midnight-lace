from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.personas import Persona


class Cliente(Base):
    __tablename__ = "clientes"

    identificador: Mapped[int] = mapped_column(Integer, ForeignKey("personas.identificador"), primary_key=True)
    numero_pais: Mapped[int | None] = mapped_column("numeroPais", Integer, ForeignKey("paises.numero"), nullable=True)
    admitido: Mapped[str | None] = mapped_column(String(2), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(10), nullable=True)
    verificador: Mapped[int] = mapped_column(Integer, ForeignKey("empleados.identificador"), nullable=False)

    persona: Mapped[Persona] = relationship("Persona")
