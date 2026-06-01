from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SolicitudCrearPuja(BaseModel):
    importe: Decimal = Field(ge=Decimal("0.01"))
    id_medio_de_pago: int = Field(alias="idMedioDePago")

    model_config = {"populate_by_name": True}


class PujaResponse(BaseModel):
    identificador: int
    id_cliente: int = Field(alias="idCliente")
    id_item: int = Field(alias="idItem")
    importe: str
    ganador: str | None = None
    realizada_en: datetime | None = Field(None, alias="realizadaEn")
    subasta: dict | None = None
    producto: dict | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class EstadoPujaActualResponse(BaseModel):
    id_item: int = Field(alias="idItem")
    descripcion_producto: str | None = Field(None, alias="descripcionProducto")
    precio_base: str = Field(alias="precioBase")
    mejor_oferta: str | None = Field(None, alias="mejorOferta")
    puja_minima: str = Field(alias="pujaMinima")
    puja_maxima: str | None = Field(None, alias="pujaMaxima")
    finaliza_en: datetime | None = Field(None, alias="finalizaEn")

    model_config = {"from_attributes": True, "populate_by_name": True}
