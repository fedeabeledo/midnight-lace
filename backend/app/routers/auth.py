from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import (
    RespuestaLogin,
    RespuestaRegistro,
    RespuestaSolicitudCodigo,
    SolicitudCambiarClave,
    SolicitudConfirmarCuenta,
    SolicitudLogin,
    SolicitudRecuperarClave,
    SolicitudRenovarToken,
    SolicitudReenviarCodigo,
)
from app.services import auth as auth_service
from app.services import email as email_service

router = APIRouter(prefix="/v1/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=RespuestaRegistro,
    status_code=status.HTTP_200_OK,
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

    if result is None:
        return RespuestaRegistro(
            aprobado=False,
            mensaje="Los datos no son válidos o el email/usuario ya está registrado.",
            email=None,
        )

    verificacion = await auth_service.verificar_cliente(db, result)
    aprobado = verificacion["aprobado"]
    codigo = verificacion["codigo"]
    categoria = verificacion["categoria"]

    if aprobado:
        await email_service.send_email(email, "registro", codigo=codigo)
        mensaje = f"Fuiste aceptado con categoría {categoria}. Revisá tu email para obtener el código de confirmación."
    else:
        await email_service.send_email(email, "rechazo", motivo="Tu solicitud no cumple con los requisitos de verificación.")
        mensaje = "Tu solicitud fue rechazada. Contactanos a soporte@midnightlace.com para más información."

    return RespuestaRegistro(
        aprobado=aprobado,
        mensaje=mensaje,
        email=email,
        categoria=categoria,
    )


@router.post(
    "/confirmar",
    response_model=RespuestaLogin,
    responses={
        400: {
            "description": "Código inválido, usado o expirado",
            "content": {
                "application/json": {
                    "examples": {
                        "CODIGO_INVALIDO": {
                            "value": {"codigo": "CODIGO_INVALIDO", "mensaje": "El código es incorrecto."}
                        },
                        "CODIGO_USADO": {
                            "value": {"codigo": "CODIGO_USADO", "mensaje": "Este código ya fue utilizado."}
                        },
                        "CODIGO_EXPIRADO": {
                            "value": {"codigo": "CODIGO_EXPIRADO", "mensaje": "El código expiró. Solicitá uno nuevo."}
                        },
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
    """Confirma registro (tipo='registro') o recuperación de clave (tipo='recuperacion')."""
    result = await auth_service.confirmar_cuenta(db, body.codigo, body.clave, body.tipo)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo": "CODIGO_INVALIDO",
                "mensaje": "El código es incorrecto.",
            },
        )

    if "error" in result:
        mensajes = {
            "CODIGO_INVALIDO": "El código es incorrecto.",
            "CODIGO_USADO": "Este código ya fue utilizado.",
            "CODIGO_EXPIRADO": "El código expiró. Solicitá uno nuevo.",
            "CLIENTE_NO_ADMITIDO": "Tu solicitud no fue aprobada.",
            "CLIENTE_INACTIVO": "Tu cuenta está inactiva.",
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo": result["error"],
                "mensaje": mensajes.get(result["error"], "Error desconocido."),
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
    status_code=status.HTTP_202_ACCEPTED,
)
async def recuperar_clave(
    body: SolicitudRecuperarClave,
    db: AsyncSession = Depends(get_db),
):
    """Envía código de recuperación por email. Siempre retorna 202 para evitar enumeración."""
    await auth_service.recuperar_clave(db, body.email)
    return {
        "mensaje": "Si el email existe, recibirás un código de recuperación."
    }


@router.post(
    "/reenviar-codigo",
    responses={
        429: {
            "description": "Rate limit excedido",
            "content": {
                "application/json": {
                    "example": {
                        "codigo": "RATE_LIMIT",
                        "mensaje": "Debés esperar 45 segundos antes de pedir un nuevo código.",
                        "segundosRestantes": 45,
                    }
                }
            },
        }
    },
)
async def reenviar_codigo(
    body: SolicitudReenviarCodigo,
    db: AsyncSession = Depends(get_db),
):
    """Reenvía código de verificación (registro o recuperación)."""
    resultado = await auth_service.reenviar_codigo(db, body.email, body.tipo)

    if not resultado["existe"]:
        return {
            "mensaje": "Si el email existe, recibirás un nuevo código."
        }

    if resultado["rate_limit"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "codigo": "RATE_LIMIT",
                "mensaje": f"Debés esperar {resultado['segundos_restantes']} segundos antes de pedir un nuevo código.",
                "segundosRestantes": resultado["segundos_restantes"],
            },
        )

    return {
        "mensaje": "Si el email existe, recibirás un nuevo código."
    }
