from datetime import date

from pydantic import BaseModel, Field


class PaisPerfil(BaseModel):
    numero: int
    nombre: str
    nombre_corto: str | None = Field(None, alias="nombreCorto")
    capital: str
    nacionalidad: str
    idiomas: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class PerfilResponse(BaseModel):
    identificador: int
    documento: str
    nombre: str
    apellido: str
    nombre_usuario: str = Field(alias="nombreUsuario")
    email: str
    direccion: str
    altura: str
    departamento: str | None = None
    localidad: str
    ciudad: str
    estado: str
    url_foto_doc_frente: str = Field(alias="urlFotoDocFrente")
    url_foto_doc_dorso: str = Field(alias="urlFotoDocDorso")
    fecha_actualizacion_foto_dni: date = Field(alias="fechaActualizacionFotoDni")
    url_foto_perfil: str | None = Field(None, alias="urlFotoPerfil")
    pais: PaisPerfil | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}
