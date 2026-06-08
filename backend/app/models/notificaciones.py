from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    persona: Mapped[int] = mapped_column(Integer, ForeignKey("personas.identificador"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    leida: Mapped[str] = mapped_column(String(2), nullable=False, default="no")
    creada_en: Mapped[datetime] = mapped_column("creadaEn", DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    detalle: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
