from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from server.core import SessionDep
from server.core.spi.base.users import SPIBaseUsers
from server.core.auth.keep_secret import read_token
from server.schemas.base.auth import CurrentUser

security = HTTPBearer(auto_error=False)

spi_users = SPIBaseUsers()


class AuthUser:
    """Clase para almacenar el usuario autenticado"""

    def __init__(self, user_data: dict):
        self.uid = user_data.get("uid")
        self.email = user_data.get("email")
        self.name = user_data.get("name")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: SessionDep = None,
) -> CurrentUser:
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    Se usa como: current_user: CurrentUser = Depends(get_current_user)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decodificar y verificar el token
        user_data = await read_token(credentials.credentials)

        # Buscar usuario en la base de datos
        from uuid import UUID

        user = await spi_users.get_user_by_id(UUID(user_data["uid"]), session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado"
            )

        if not user.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
            )

        # Obtener scopes y groups
        scopes = [scope.name for scope in user.scopes] if user.scopes else []
        groups = [group.name for group in user.groups] if user.groups else []

        return CurrentUser(
            id=user.id,
            name=user.name,
            email=user.email,
            active=user.active,
            scopes=scopes,
            groups=groups,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: SessionDep = None,
) -> Optional[CurrentUser]:
    """
    Dependencia opcional - retorna None si no hay token válido.
    Útil para endpoints públicos que pueden comportarse diferente si hay auth.
    """
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
