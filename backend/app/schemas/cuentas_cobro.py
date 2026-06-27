from pydantic import BaseModel, Field


class SolicitudCrearCuentaCobro(BaseModel):
    nombre_banco: str = Field(alias="nombreBanco")
    numero_cuenta: str = Field(alias="numeroCuenta")
    moneda: str
    id_pais: int | None = Field(None, alias="idPais")

    model_config = {"populate_by_name": True}
