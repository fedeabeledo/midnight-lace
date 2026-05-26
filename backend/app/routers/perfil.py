from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.schemas.perfil import PerfilResponse
from app.services import perfil as perfil_service
from app.services.auth import save_upload

router = APIRouter(prefix="/v1/perfil", tags=["Perfil"])


@router.get("", response_model=PerfilResponse)
async def ver_perfil(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await perfil_service.get_perfil(db, user["identificador"])
    return data


@router.patch("", response_model=PerfilResponse)
async def actualizar_perfil(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    nombre: str | None = Form(None),
    apellido: str | None = Form(None),
    email: str | None = Form(None),
    nombreUsuario: str | None = Form(None),
    direccion: str | None = Form(None),
    altura: str | None = Form(None),
    departamento: str | None = Form(None),
    localidad: str | None = Form(None),
    ciudad: str | None = Form(None),
    idPais: int | None = Form(None),
    fotoPerfil: UploadFile | None = File(None),
    fotoDocFrente: UploadFile | None = File(None),
    fotoDocDorso: UploadFile | None = File(None),
):
    kwargs = {}

    for field, val in [
        ("nombre", nombre), ("apellido", apellido), ("email", email),
        ("nombre_usuario", nombreUsuario), ("direccion", direccion),
        ("altura", altura), ("departamento", departamento),
        ("localidad", localidad), ("ciudad", ciudad),
    ]:
        if val is not None:
            kwargs[field] = val

    if fotoPerfil is not None:
        kwargs["url_foto_perfil"] = save_upload(
            await fotoPerfil.read(), f"{user['email']}_perfil.jpg"
        )
    if fotoDocFrente is not None:
        kwargs["url_foto_doc_frente"] = save_upload(
            await fotoDocFrente.read(), f"{user['email']}_frente.jpg"
        )
    if fotoDocDorso is not None:
        kwargs["url_foto_doc_dorso"] = save_upload(
            await fotoDocDorso.read(), f"{user['email']}_dorso.jpg"
        )

    if idPais is not None:
        kwargs["numero_pais"] = idPais

    return await perfil_service.update_perfil(db, user["identificador"], **kwargs)
