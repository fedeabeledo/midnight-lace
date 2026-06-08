from pydantic import BaseModel


class PaisResponse(BaseModel):
    numero: int
    nombre: str
    nombre_corto: str | None = None
    capital: str
    nacionalidad: str
    idiomas: str

    model_config = {"from_attributes": True}


class MetaPaginacion(BaseModel):
    pagina: int
    cantidad: int
    total: int
    total_paginas: int


class PaginaPaises(BaseModel):
    datos: list[PaisResponse]
    meta: MetaPaginacion
