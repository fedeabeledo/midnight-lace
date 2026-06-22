from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChequeCertificado, MedioDePago


async def procesar_pago(
    db: AsyncSession,
    user_id: int,
    medio_id: int,
    monto: Decimal,
    moneda: str,
) -> None:
    medio = await db.get(MedioDePago, medio_id)
    if medio is None or medio.cliente != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"codigo": "MEDIO_NO_ENCONTRADO", "mensaje": "Medio de pago no encontrado."},
        )
    if medio.verificado != "si":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "MEDIO_PAGO_NO_VERIFICADO", "mensaje": "El medio de pago no está verificado."},
        )
    if medio.activo != "si":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "MEDIO_PAGO_INACTIVO", "mensaje": "El medio de pago está inactivo."},
        )
    if medio.moneda != moneda:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo": "MONEDA_NO_COINCIDE", "mensaje": f"El medio opera en {medio.moneda}, no en {moneda}."},
        )

    if medio.tipo == "chequeCertificado":
        cheque = await db.scalar(
            select(ChequeCertificado).where(ChequeCertificado.medio_pago == medio_id)
        )
        if cheque is None or cheque.monto_disponible < monto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"codigo": "PUJA_CHEQUE_SIN_FONDOS", "mensaje": "Fondos insuficientes en el cheque certificado."},
            )
        cheque.monto_disponible -= monto
