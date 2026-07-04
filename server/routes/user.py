from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr

from libs.fastapi_crudrouter import SQLModelAsyncCRUDRouter

from core import SessionDep
from core.spi.base.users import SPIBaseUsers, get_session
from core.auth.dependencies import get_current_user
from server.schemas.base.auth import CurrentUser
from server.schemas.base.user import BaseUserSchema

router = APIRouter(
    prefix="/user",
    tags=["Users"],
    dependencies=[Depends(get_current_user)], #TODO: agregar estas validaciones
)
spi_users = SPIBaseUsers()

crud_router = SQLModelAsyncCRUDRouter(
    schema=BaseUserSchema,
    db_model=spi_users.user_class,
    model_id_field="id",
    model_name="user",
    db=get_session,
    delete_all_route=False,
    get_all_route=False
)

router.include_router(crud_router)

@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Obtener información del usuario actual autenticado.
    Equivalente a /auth/me pero en el contexto de /user.
    """
    return current_user

@router.put("/me", response_model=CurrentUser)
async def update_current_user(
    session: SessionDep,
    name: Optional[str] = None,
    email: Optional[EmailStr] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Actualizar información del usuario actual.
    Solo actualiza los campos proporcionados (partial update).
    """
    try:
        user = await spi_users.get_user_by_id(UUID(str(current_user.id)), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        if name is not None:
            user.name = name
        if email is not None:
            existing = await spi_users.get_user_by_email(email, session)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está en uso",
                )
            user.email = email

        updated_user = await spi_users.update_user(user, session)

        scopes = (
            [scope.name for scope in updated_user.scopes] if updated_user.scopes else []
        )
        groups = (
            [group.name for group in updated_user.groups] if updated_user.groups else []
        )

        return CurrentUser(
            id=updated_user.id,
            name=updated_user.name,
            email=updated_user.email,
            active=updated_user.active,
            scopes=scopes,
            groups=groups,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}",
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    session: SessionDep, current_user: CurrentUser = Depends(get_current_user),
):
    """
    Eliminar la cuenta del usuario actual (soft delete - desactivar).
    Para hard delete, descomenta la línea de eliminación.
    """
    try:

        user = await spi_users.get_user_by_id(current_user.id, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        user.active = False
        await spi_users.update_user(user, session)

        # await spi_users.delete_user(user.id, session)

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar usuario: {str(e)}",
        )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    session: SessionDep,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Cambiar la contraseña del usuario actual.
    """
    try:
        user = await spi_users.get_user_by_id(UUID(str(current_user.id)), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        try:
            user.verify_password(current_password)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta",
            )

        await spi_users.change_password(user, new_password, session)

        return {"message": "Contraseña actualizada correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar contraseña: {str(e)}",
        )
