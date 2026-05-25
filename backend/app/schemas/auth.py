from pydantic import BaseModel, EmailStr, Field, field_validator


class SolicitudRegistro(BaseModel):
    documento: str
    nombre: str
    apellido: str
    email: EmailStr
    nombre_usuario: str
    direccion: str
    altura: str
    departamento: str | None = None
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
    token_acceso: str = Field(alias="tokenAcceso")
    token_renovacion: str = Field(alias="tokenRenovacion")
    roles: list[str]
    multa_impaga: bool = Field(alias="multaImpaga")

    model_config = {"populate_by_name": True}


class SolicitudRenovarToken(BaseModel):
    token_renovacion: str = Field(alias="tokenRenovacion")


class SolicitudCambiarClave(BaseModel):
    clave_actual: str = Field(alias="claveActual")
    clave_nueva: str = Field(alias="claveNueva")

    @field_validator("clave_nueva")
    @classmethod
    def clave_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La clave nueva debe tener al menos 8 caracteres.")
        return v

    model_config = {"populate_by_name": True}


class SolicitudRecuperarClave(BaseModel):
    email: EmailStr
