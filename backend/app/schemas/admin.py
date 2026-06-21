from typing import Literal

from pydantic import BaseModel, Field


CATEGORIAS_VALIDAS = {"comun", "especial", "plata", "oro", "platino"}


class SolicitudActualizarCliente(BaseModel):
    admitido: Literal["si", "no"] | None = None
    categoria: str | None = None

    def model_post_init(self, __context):
        if self.categoria is not None and self.categoria not in CATEGORIAS_VALIDAS:
            raise ValueError(f"categoria debe ser una de: {', '.join(sorted(CATEGORIAS_VALIDAS))}")


class SolicitudCrearSubastador(BaseModel):
    documento: str
    nombre: str
    apellido: str
    email: str
    nombre_usuario: str = Field(alias="nombreUsuario")
    clave: str = Field(min_length=8)
    matricula: str | None = None
    region: str | None = None

    model_config = {"populate_by_name": True}
