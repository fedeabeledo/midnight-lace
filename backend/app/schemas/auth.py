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
    aprobado: bool
    mensaje: str
    email: EmailStr | None = None
    categoria: str | None = None


class SolicitudConfirmarCuenta(BaseModel):
    codigo: str = Field(min_length=6, max_length=6)
    clave: str
    tipo: str = "registro"

    @field_validator("codigo")
    @classmethod
    def codigo_solo_numeros(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El código debe contener solo dígitos.")
        return v

    @field_validator("clave")
    @classmethod
    def clave_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La clave debe tener al menos 8 caracteres.")
        return v

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        if v not in ("registro", "recuperacion"):
            raise ValueError("Tipo debe ser 'registro' o 'recuperacion'.")
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


class SolicitudReenviarCodigo(BaseModel):
    email: EmailStr
    tipo: str = Field(default="registro")

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        if v not in ("registro", "recuperacion"):
            raise ValueError("Tipo debe ser 'registro' o 'recuperacion'.")
        return v


class RespuestaSolicitudCodigo(BaseModel):
    mensaje: str
