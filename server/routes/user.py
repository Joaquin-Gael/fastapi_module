from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr

from server.core import SessionDep
from server.core.spi.base.users import SPIBaseUsers
from server.core.auth.dependencies import get_current_user, AuthUser
from server.schemas.base.auth import CurrentUser

router = APIRouter(prefix="/user", tags=["User"])
spi_users = SPIBaseUsers()


@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Obtener información del usuario actual autenticado.
    Equivalente a /auth/me pero en el contexto de /user.
    """
    return current_user


@router.put("/me", response_model=CurrentUser)
async def update_current_user(
    name: Optional[str] = None,
    email: Optional[EmailStr] = None,
    current_user: CurrentUser = Depends(get_current_user),
    session: SessionDep = None,
):
    """
    Actualizar información del usuario actual.
    Solo actualiza los campos proporcionados (partial update).
    """
    try:
        from uuid import UUID as U

        user = await spi_users.get_user_by_id(U(str(current_user.id)), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        # Actualizar solo los campos proporcionados
        if name is not None:
            user.name = name
        if email is not None:
            # Verificar que el nuevo email no esté en uso
            existing = await spi_users.get_user_by_email(email, session)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está en uso",
                )
            user.email = email

        updated_user = await spi_users.update_user(user, session)

        # Retornar con scopes y groups
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
    current_user: CurrentUser = Depends(get_current_user), session: SessionDep = None
):
    """
    Eliminar la cuenta del usuario actual (soft delete - desactivar).
    Para hard delete, descomenta la línea de eliminación.
    """
    try:
        from uuid import UUID as U

        user = await spi_users.get_user_by_id(U(str(current_user.id)), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        # Soft delete: desactivar usuario
        user.active = False
        await spi_users.update_user(user, session)

        # Hard delete (descomenta si necesitas eliminar físicamente):
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
    current_user: CurrentUser = Depends(get_current_user),
    session: SessionDep = None,
):
    """
    Cambiar la contraseña del usuario actual.
    """
    try:
        from uuid import UUID as U
        from server.core.models.base.user import hasher, User

        user = await spi_users.get_user_by_id(U(str(current_user.id)), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        # Verificar contraseña actual
        try:
            hasher.verify(user.password, current_password)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta",
            )

        # El setter de password se encarga de validar y hashear
        user.password = new_password
        await spi_users.update_user(user, session)

        return {"message": "Contraseña actualizada correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar contraseña: {str(e)}",
        )
