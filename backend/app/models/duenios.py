from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.personas import Persona


class Duenio(Base):
    __tablename__ = "duenios"

    identificador: Mapped[int] = mapped_column(Integer, ForeignKey("personas.identificador"), primary_key=True)
    numero_pais: Mapped[int | None] = mapped_column("numeroPais", Integer, ForeignKey("paises.numero"), nullable=True)
    verificacion_financiera: Mapped[str | None] = mapped_column("verificacionFinanciera", String(2), nullable=True)
    verificacion_judicial: Mapped[str | None] = mapped_column("verificacionJudicial", String(2), nullable=True)
    calificacion_riesgo: Mapped[int | None] = mapped_column("calificacionRiesgo", Integer, nullable=True)
    verificador: Mapped[int] = mapped_column(Integer, ForeignKey("empleados.identificador"), nullable=False)

    persona: Mapped[Persona] = relationship("Persona")
