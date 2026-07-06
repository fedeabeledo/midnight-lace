from datetime import date, time, datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.productos import FotoResponse


class SubastaResponse(BaseModel):
    identificador: int
    nombre: str
    fecha: date | None = None
    hora: str | None = None
    estado: str | None = None
    id_subastador: int | None = Field(None, alias="idSubastador")
    ubicacion: str
    capacidad_asistentes: int | None = Field(None, alias="capacidadAsistentes")
    tiene_deposito: str | None = Field(None, alias="tieneDeposito")
    seguridad_propia: str | None = Field(None, alias="seguridadPropia")
    categoria: str | None = None
    moneda: str | None = None
    duracion_item_minutos: int | None = Field(None, alias="duracionItemMinutos")
    foto_principal: str | None = Field(None, alias="fotoPrincipal")

    model_config = {"from_attributes": True, "populate_by_name": True}


class SolicitudCrearSubasta(BaseModel):
    nombre: str
    fecha: date
    hora: str
    ubicacion: str
    capacidad_asistentes: int | None = Field(None, alias="capacidadAsistentes")
    tiene_deposito: Literal["si", "no"] | None = Field(None, alias="tieneDeposito")
    seguridad_propia: Literal["si", "no"] | None = Field(None, alias="seguridadPropia")
    categoria: Literal["comun", "especial", "plata", "oro", "platino"]
    moneda: Literal["ARS", "USD"]
    duracion_item_minutos: int = Field(alias="duracionItemMinutos", ge=1)

    model_config = {"populate_by_name": True}

    @field_validator("ubicacion")
    @classmethod
    def ubicacion_obligatoria(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La ubicacion es obligatoria.")
        return v.strip()

    @field_validator("fecha")
    @classmethod
    def fecha_futura(cls, v: date) -> date:
        # if v <= date.today() + timedelta(days=10):
        #     raise ValueError("La fecha debe ser al menos 10 días posterior a hoy.")
        return v


class SolicitudActualizarSubasta(BaseModel):
    fecha: date | None = None
    hora: str | None = None
    ubicacion: str | None = None
    capacidad_asistentes: int | None = Field(None, alias="capacidadAsistentes")
    tiene_deposito: Literal["si", "no"] | None = Field(None, alias="tieneDeposito")
    seguridad_propia: Literal["si", "no"] | None = Field(None, alias="seguridadPropia")
    duracion_item_minutos: int | None = Field(None, alias="duracionItemMinutos", ge=1)

    model_config = {"populate_by_name": True}


class SolicitudCambiarEstado(BaseModel):
    estado: Literal["abierta", "cerrada"]


class SolicitudCrearCatalogo(BaseModel):
    descripcion: str
    id_subasta: int = Field(alias="idSubasta")

    model_config = {"populate_by_name": True}


class SolicitudAgregarItemCatalogo(BaseModel):
    id_producto: int = Field(alias="idProducto")
    orden: int
    comision: Decimal = Field(ge=Decimal("0.01"))

    model_config = {"populate_by_name": True}


class ItemCatalogoResponse(BaseModel):
    identificador: int
    id_producto: int = Field(alias="idProducto")
    nombre: str | None = None
    estado: Literal["nuevo", "usado"] | None = None
    fotos: list[FotoResponse] = Field(default_factory=list, max_length=1)
    descripcion_catalogo: str | None = Field(None, alias="descripcionCatalogo")
    precio_base: str | None = Field(None, alias="precioBase")
    orden: int
    comision: str
    subastado: str | None = None
    iniciado_en: datetime | None = Field(None, alias="iniciadoEn")
    finalizado_en: datetime | None = Field(None, alias="finalizadoEn")

    model_config = {"from_attributes": True, "populate_by_name": True}


class CatalogoMetaResponse(BaseModel):
    pagina: int
    cantidad: int
    total: int
    total_paginas: int


class CatalogoResponse(BaseModel):
    identificador: int
    descripcion: str
    id_subasta: int | None = Field(None, alias="idSubasta")
    id_subastador: int | None = Field(None, alias="idSubastador")
    items: list[ItemCatalogoResponse] = []
    meta: CatalogoMetaResponse | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}
