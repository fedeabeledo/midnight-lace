from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models import Cliente, Duenio, Empleado, Subastador
from app.models.personas import Persona

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "NO_AUTENTICADO",
                "mensaje": "No autenticado. Iniciá sesión para continuar.",
            },
        )
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "NO_AUTENTICADO",
                "mensaje": "Token inválido o expirado.",
            },
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "NO_AUTENTICADO",
                "mensaje": "Token inválido o expirado.",
            },
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "NO_AUTENTICADO",
                "mensaje": "Token inválido.",
            },
        )

    user_id = int(sub)

    resultado = await db.execute(select(Persona).where(Persona.identificador == user_id))
    persona = resultado.scalar_one_or_none()
    if persona is None or persona.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "NO_AUTENTICADO",
                "mensaje": "Usuario no encontrado o inactivo.",
            },
        )

    roles = []
    if await db.scalar(select(Cliente).where(Cliente.identificador == user_id)):
        roles.append("comprador")
    if await db.scalar(select(Duenio).where(Duenio.identificador == user_id)):
        roles.append("duenio")
    if await db.scalar(select(Subastador).where(Subastador.identificador == user_id)):
        roles.append("subastador")
    if await db.scalar(select(Empleado).where(Empleado.identificador == user_id)):
        roles.append("empleado")

    return {
        "identificador": user_id,
        "roles": roles,
        "email": persona.email,
        "nombre": persona.nombre,
        "multa_impaga": payload.get("multaImpaga", False),
    }


def require_role(*roles: str):
    async def dependency(user: dict = Depends(get_current_user)):
        user_roles = set(user.get("roles", []))
        required = set(roles)
        if not user_roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "codigo": "SIN_PERMISO",
                    "mensaje": "No tenés permisos para realizar esta acción.",
                },
            )
        return user

    return dependency
