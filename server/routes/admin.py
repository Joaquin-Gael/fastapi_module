import json

from fastapi import APIRouter, Form, Request, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from server.config import Settings
from server.core.cache import rc
from server.core.utils.logger import get_logger
from server.forms.logs import LogsFilterForm
from server.templates.utils import get_template
from server.core.spi.base.logs import SPILogs
from server.core.spi.base.users import SPIBaseUsers
from server.core import SessionDep
from server.core.auth.dependencies import get_current_user
from server.schemas.base.logs import BaseLogSchema
from server.schemas.base.auth import CurrentUser

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

spi_logs = SPILogs()
spi_users = SPIBaseUsers()


class UserListResponse(BaseModel):
    id: str
    name: str
    email: str
    active: bool


class UserUpdateRequest(BaseModel):
    active: Optional[bool] = None
    name: Optional[str] = None


@router.get("/")
async def models(request: Request) -> list:
    raw_members = await rc.smembers("admin:registry")
    result: list[dict] = []
    for raw in raw_members:
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            data.pop("model_module", None)
            result.append(data)
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error("Failed to parse model %s: %s", raw, e)
    return result


@router.post("/logs")
async def read_logs(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser = Depends(get_current_user),
    filter_form: LogsFilterForm = Form(...),
):
    try:
        logs = await spi_logs.get_logs(
            session,
            filter_form.offset or 0,
            filter_form.limit or 100,
            filter_form.word_key,
        )
        return [BaseLogSchema.from_orm(log) for log in logs]

    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"Error": "Not able to read logs"}


# ===== Endpoints de gestión de usuarios =====


@router.get("/users", response_model=list[UserListResponse])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
    session: SessionDep = None,
):
    """Listar todos los usuarios (solo admins) - USA SPI"""
    try:
        users = await spi_users.get_users(session, limit=limit, offset=offset)

        return [
            UserListResponse(
                id=str(user.id), name=user.name, email=user.email, active=user.active
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar usuarios",
        )


@router.get("/users/{user_id}", response_model=UserListResponse)
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: SessionDep = None,
):
    """Obtener detalle de un usuario específico - USA SPI"""
    try:
        from uuid import UUID

        user = await spi_users.get_user_by_id(UUID(user_id), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        return UserListResponse(
            id=str(user.id), name=user.name, email=user.email, active=user.active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener usuario",
        )


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: SessionDep = None,
):
    """Actualizar usuario (activar/desactivar, cambiar nombre) - USA SPI"""
    try:
        from uuid import UUID

        user = await spi_users.get_user_by_id(UUID(user_id), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        if update_data.active is not None:
            user.active = update_data.active
        if update_data.name is not None:
            user.name = update_data.name

        updated_user = await spi_users.update_user(user, session)

        return {
            "id": str(updated_user.id),
            "name": updated_user.name,
            "email": updated_user.email,
            "active": updated_user.active,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar usuario",
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: SessionDep = None,
):
    """Eliminar usuario (soft delete - desactivar) - USA SPI"""
    try:
        from uuid import UUID

        user = await spi_users.get_user_by_id(UUID(user_id), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )

        # No permitir que un admin se elimine a sí mismo
        if str(user.id) == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propia cuenta",
            )

        # Soft delete
        user.active = False
        await spi_users.update_user(user, session)

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar usuario",
        )
