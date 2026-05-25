from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Pais(Base):
    __tablename__ = "paises"

    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(250), nullable=False)
    nombre_corto: Mapped[str | None] = mapped_column("nombreCorto", String(250), nullable=True)
    capital: Mapped[str] = mapped_column(String(250), nullable=False)
    nacionalidad: Mapped[str] = mapped_column(String(250), nullable=False)
    idiomas: Mapped[str] = mapped_column(String(150), nullable=False)
