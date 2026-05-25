import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import EmailStr, field_validator
from pydantic import BaseModel


class SolicitudRegistro(BaseModel):
    documento: str
    nombre: str
    apellido: str
    email: EmailStr
    nombre_usuario: str
    direccion: str
    altura: str
    departamento: Optional[str] = None
    localidad: str
    ciudad: str
    id_pais: int


class RespuestaRegistro(BaseModel):
    mensaje: str = "Solicitud recibida. Si los datos son válidos, recibirás un email para completar el registro."


class SolicitudConfirmarCuenta(BaseModel):
    token: str
    clave: str

    @field_validator("clave")
    @classmethod
    def clave_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La clave debe tener al menos 8 caracteres.")
        return v


class SolicitudLogin(BaseModel):
    email: EmailStr
    clave: str


class RespuestaLogin(BaseModel):
    token_acceso: str
    token_renovacion: str
    roles: list[str]
    multa_impaga: bool


class SolicitudRenovarToken(BaseModel):
    token_renovacion: str


class SolicitudCambiarClave(BaseModel):
    clave_actual: str
    clave_nueva: str

    @field_validator("clave_nueva")
    @classmethod
    def clave_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La clave nueva debe tener al menos 8 caracteres.")
        return v


class SolicitudRecuperarClave(BaseModel):
    email: EmailStr
