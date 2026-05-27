from datetime import date

from pydantic import BaseModel, Field


class FotoResponse(BaseModel):
    identificador: int
    foto: str
    orden: int

    model_config = {"from_attributes": True}


class DetalleArtisticoResponse(BaseModel):
    artista: str
    fecha_obra: date | None = Field(None, alias="fechaObra")
    historia: str | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ComponenteResponse(BaseModel):
    identificador: int
    descripcion: str
    cantidad: int

    model_config = {"from_attributes": True}


class SeguroResponse(BaseModel):
    nro_poliza: str = Field(alias="nroPoliza")
    compania: str
    poliza_combinada: str | None = Field(None, alias="polizaCombinada")
    importe: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class DepositoResponse(BaseModel):
    identificador: int
    nombre: str
    direccion: str

    model_config = {"from_attributes": True}


class ProductoResponse(BaseModel):
    identificador: int
    fecha: date | None = None
    disponible: str | None = None
    descripcion_catalogo: str | None = Field(None, alias="descripcionCatalogo")
    descripcion_completa: str = Field(alias="descripcionCompleta")
    precio_base: str = Field(alias="precioBase")
    estado_producto: str = Field(alias="estadoProducto")
    declaracion_propiedad: bool = Field(alias="declaracionPropiedad")
    fotos: list[FotoResponse] = []
    detalle_artistico: DetalleArtisticoResponse | None = Field(None, alias="detalleArtistico")
    componentes: list[ComponenteResponse] = []
    seguro: SeguroResponse | None = None
    deposito: DepositoResponse | None = None
    motivo_rechazo: str | None = Field(None, alias="motivoRechazo")

    model_config = {"from_attributes": True, "populate_by_name": True}


class SolicitudAceptarCondiciones(BaseModel):
    acepta: bool
