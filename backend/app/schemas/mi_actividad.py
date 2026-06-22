from pydantic import BaseModel


class SolicitudPagarCompra(BaseModel):
    idMedioPago: int


class SolicitudRetiro(BaseModel):
    retiraPersonalmente: bool


class SolicitudPagarMulta(BaseModel):
    idMedioPago: int


class SolicitudMarcarLeida(BaseModel):
    leida: bool
