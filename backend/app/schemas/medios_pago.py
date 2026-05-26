from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


TIPO_CAMPOS = {
    "cuentaBancaria": ["nombreBanco", "numeroCuenta"],
    "tarjetaCredito": ["ultimosCuatroDigitos", "nombreTitular", "fechaVencimiento"],
    "chequeCertificado": ["montoGarantizado", "montoDisponible", "fechaEntrega"],
}


class DetalleCuentaBancaria(BaseModel):
    nombre_banco: str = Field(alias="nombreBanco")
    numero_cuenta: str = Field(alias="numeroCuenta")
    id_pais: int | None = Field(None, alias="idPais")

    model_config = {"populate_by_name": True}


class DetalleTarjetaCredito(BaseModel):
    ultimos_cuatro_digitos: str = Field(
        alias="ultimosCuatroDigitos",
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
    )
    nombre_titular: str = Field(alias="nombreTitular")
    fecha_vencimiento: date = Field(alias="fechaVencimiento")
    red: str | None = None
    es_internacional: Literal["si", "no"] = Field("no", alias="esInternacional")

    model_config = {"populate_by_name": True}


class DetalleChequeCertificado(BaseModel):
    monto_garantizado: Decimal = Field(alias="montoGarantizado", gt=0)
    monto_disponible: Decimal = Field(alias="montoDisponible", ge=0)
    fecha_entrega: date = Field(alias="fechaEntrega")

    model_config = {"populate_by_name": True}


class SolicitudAgregarMedioDePago(BaseModel):
    tipo: Literal["cuentaBancaria", "tarjetaCredito", "chequeCertificado"]
    moneda: Literal["ARS", "USD"] = "ARS"
    detalle: dict[str, Any]

    @model_validator(mode="after")
    def validar_detalle_segun_tipo(self):
        tipo = self.tipo
        raw = self.detalle

        tipo_modelo_map = {
            "cuentaBancaria": DetalleCuentaBancaria,
            "tarjetaCredito": DetalleTarjetaCredito,
            "chequeCertificado": DetalleChequeCertificado,
        }
        modelo = tipo_modelo_map[tipo]

        try:
            self.detalle = modelo(**raw)
        except ValidationError as e:
            errores = []
            for err in e.errors():
                loc = " → ".join(str(l) for l in err["loc"])
                errores.append(f"{loc}: {err['msg']}")
            campos_esperados = ", ".join(TIPO_CAMPOS[tipo])
            raise ValueError(
                f"Detalle inválido para tipo '{tipo}'. "
                f"Campos requeridos: {campos_esperados}. "
                f"Errores: {'; '.join(errores)}"
            )

        return self


class MedioDePagoResponse(BaseModel):
    identificador: int
    tipo: str
    moneda: str
    verificado: str
    activo: str
    detalle: DetalleCuentaBancaria | DetalleTarjetaCredito | DetalleChequeCertificado

    model_config = {"from_attributes": True, "populate_by_name": True}
