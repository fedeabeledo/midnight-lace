from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.personas import Persona


class Subastador(Base):
    __tablename__ = "subastadores"

    identificador: Mapped[int] = mapped_column(Integer, ForeignKey("personas.identificador"), primary_key=True)
    matricula: Mapped[str | None] = mapped_column(String(15), nullable=True)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)

    persona: Mapped[Persona] = relationship("Persona")
