from pydantic import BaseModel


class MetricasPujasPorMes(BaseModel):
    anio: int
    mes: int
    cantidad: int


class MetricasPorCategoria(BaseModel):
    categoria: str | None = None
    participaciones: int
    ganadas: int


class MetricasMiActividadResponse(BaseModel):
    totalPujas: int
    pujasGanadas: int
    totalCompras: int
    comprasPagadas: int
    multasImpagas: int
    totalSubastasParticipadas: int
    totalPujasRealizadas: int
    totalGanadas: int
    totalImportePujado: float
    totalImportePagado: float
    pujasPorMes: list[MetricasPujasPorMes]
    porCategoria: list[MetricasPorCategoria]


class SolicitudPagarCompra(BaseModel):
    idMedioPago: int


class SolicitudRetiro(BaseModel):
    retiraPersonalmente: bool


class SolicitudPagarMulta(BaseModel):
    idMedioPago: int


class SolicitudMarcarLeida(BaseModel):
    leida: bool
