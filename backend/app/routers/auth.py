from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import (
    RespuestaLogin,
    RespuestaRegistro,
    SolicitudCambiarClave,
    SolicitudConfirmarCuenta,
    SolicitudLogin,
    SolicitudRecuperarClave,
    SolicitudRenovarToken,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/v1/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=RespuestaRegistro,
    status_code=status.HTTP_202_ACCEPTED,
)
async def registro(
    documento: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...),
    nombreUsuario: str = Form(...),
    direccion: str = Form(...),
    altura: str = Form(...),
    localidad: str = Form(...),
    ciudad: str = Form(...),
    idPais: int = Form(...),
    fotoDocFrente: UploadFile = File(...),
    fotoDocDorso: UploadFile = File(...),
    departamento: str | None = Form(None),
    fotoPerfil: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.registrar_comprador(
        db=db,
        documento=documento,
        nombre=nombre,
        apellido=apellido,
        email=email,
        nombre_usuario=nombreUsuario,
        direccion=direccion,
        altura=altura,
        localidad=localidad,
        ciudad=ciudad,
        id_pais=idPais,
        foto_doc_frente=await fotoDocFrente.read(),
        foto_doc_dorso=await fotoDocDorso.read(),
        departamento=departamento,
        foto_perfil=await fotoPerfil.read() if fotoPerfil else None,
    )

    if result is not None:
        token = await auth_service.verificar_cliente(db, result)
        if token is not None:
            print(f"[REGISTRO] Cliente {result} ({email}) APROBADO automáticamente.")
            print(f"[REGISTRO] → Enviar email a {email} con link: http://localhost:8000/confirmar?token={token}")
        else:
            print(f"[REGISTRO] Cliente {result} ({email}) RECHAZADO automáticamente.")
            print(f"[REGISTRO] → Enviar email a {email} notificando el rechazo.")

    return RespuestaRegistro()


@router.post(
    "/confirmar",
    response_model=RespuestaLogin,
    responses={
        400: {
            "description": "Token inválido o expirado",
            "content": {
                "application/json": {
                    "example": {
                        "codigo": "TOKEN_INVALIDO",
                        "mensaje": "Token inválido o expirado.",
                    }
                }
            },
        }
    },
)
async def confirmar(
    body: SolicitudConfirmarCuenta,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.confirmar_cuenta(db, body.token, body.clave)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo": "TOKEN_INVALIDO",
                "mensaje": "Token inválido o expirado.",
            },
        )
    return result


@router.post(
    "/login",
    response_model=RespuestaLogin,
    responses={
        401: {
            "description": "Credenciales inválidas",
            "content": {
                "application/json": {
                    "example": {
                        "codigo": "CREDENCIALES_INVALIDAS",
                        "mensaje": "Email o contraseña incorrectos.",
                    }
                }
            },
        }
    },
)
async def login(
    body: SolicitudLogin,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.login(db, body.email, body.clave)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "CREDENCIALES_INVALIDAS",
                "mensaje": "Email o contraseña incorrectos.",
            },
        )
    return result


@router.post(
    "/renovar",
    response_model=RespuestaLogin,
    responses={
        401: {
            "description": "Token de renovación inválido",
            "content": {
                "application/json": {
                    "example": {
                        "codigo": "TOKEN_INVALIDO",
                        "mensaje": "Token de renovación inválido o expirado.",
                    }
                }
            },
        }
    },
)
async def renovar(
    body: SolicitudRenovarToken,
    db: AsyncSession = Depends(get_db),
):
    result = await auth_service.renovar_token(db, body.token_renovacion)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "TOKEN_INVALIDO",
                "mensaje": "Token de renovación inválido o expirado.",
            },
        )
    return result


@router.post(
    "/cambiar-clave",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {
            "description": "Clave actual incorrecta",
            "content": {
                "application/json": {
                    "example": {
                        "codigo": "CLAVE_INCORRECTA",
                        "mensaje": "La clave actual es incorrecta.",
                    }
                }
            },
        }
    },
)
async def cambiar_clave(
    body: SolicitudCambiarClave,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await auth_service.cambiar_clave(db, user["identificador"], body.clave_actual, body.clave_nueva)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo": "CLAVE_INCORRECTA",
                "mensaje": "La clave actual es incorrecta.",
            },
        )


@router.post(
    "/recuperar-clave",
    response_model=RespuestaRegistro,
    status_code=status.HTTP_202_ACCEPTED,
)
async def recuperar_clave(
    body: SolicitudRecuperarClave,
    db: AsyncSession = Depends(get_db),
):
    await auth_service.recuperar_clave(db, body.email)
    return RespuestaRegistro()
