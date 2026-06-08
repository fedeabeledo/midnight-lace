from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodigoVerificacion(Base):
    __tablename__ = "codigosVerificacion"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    persona: Mapped[int] = mapped_column(Integer, ForeignKey("personas.identificador"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(6), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    creado_en: Mapped[datetime] = mapped_column("creadoEn", DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expira_en: Mapped[datetime] = mapped_column("expiraEn", DateTime(timezone=True), nullable=False)
    usado: Mapped[str] = mapped_column(String(2), nullable=False, default="no")
