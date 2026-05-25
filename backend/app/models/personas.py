from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Persona(Base):
    __tablename__ = "personas"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    documento: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    apellido: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    nombre_usuario: Mapped[str] = mapped_column("nombreUsuario", String(50), nullable=False, unique=True)
    direccion: Mapped[str | None] = mapped_column(String(250), nullable=True)
    altura: Mapped[str] = mapped_column(String(10), nullable=False)
    departamento: Mapped[str | None] = mapped_column(String(20), nullable=True)
    localidad: Mapped[str] = mapped_column(String(150), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(150), nullable=False)
    estado: Mapped[str] = mapped_column(String(15), nullable=False, default="pendiente")
    url_foto_doc_frente: Mapped[str] = mapped_column("urlFotoDocFrente", String(500), nullable=False)
    url_foto_doc_dorso: Mapped[str] = mapped_column("urlFotoDocDorso", String(500), nullable=False)
    fecha_actualizacion_foto_dni: Mapped[date] = mapped_column(
        "fechaActualizacionFotoDni", Date, nullable=False, default=date.today
    )
    url_foto_perfil: Mapped[str | None] = mapped_column("urlFotoPerfil", String(500), nullable=True)
    hash_contrasenia: Mapped[str | None] = mapped_column("hashContrasenia", String(500), nullable=True)


class Sector(Base):
    __tablename__ = "sectores"

    identificador: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_sector: Mapped[str] = mapped_column("nombreSector", String(150), nullable=False)
    codigo_sector: Mapped[str | None] = mapped_column("codigoSector", String(10), nullable=True)
    responsable_sector: Mapped[int | None] = mapped_column("responsableSector", Integer, ForeignKey("empleados.identificador"), nullable=True)


class Empleado(Base):
    __tablename__ = "empleados"

    identificador: Mapped[int] = mapped_column(Integer, ForeignKey("personas.identificador"), primary_key=True)
    cargo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector: Mapped[int | None] = mapped_column(Integer, ForeignKey("sectores.identificador"), nullable=True)

    persona: Mapped[Persona] = relationship("Persona")
