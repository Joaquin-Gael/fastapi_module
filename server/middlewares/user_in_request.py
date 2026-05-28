from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from server.config import Settings
from core.utils.logger import get_logger
from core.database.main import engine, AsyncSession
from sqlmodel import select

logger = get_logger(__name__)

# PORGRAMER_MESSAGE: se tiene que simular una clase que está relacionada con la clase base de usuarios
# donde se gestiona la sesión en la DB y mantiene una sesión por usuario y su información.
# Esa tabla maneja todas las sesiones y después de un tiempo se "apagan" y se tiene que volver a verificar el usuario.


class UserInRequestSessionMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts a token from the Authorization header, looks up the
    corresponding user in the database and attaches it to ``request.state.user``.

    ``user_class``: SQLModel model class representing the user table.
    ``keys``: list of attribute names of ``user_class`` used to match the token.
    The first key is used for the lookup.
    """

    def __init__(self, app: ASGIApp, user_class, keys: list[str]):
        super().__init__(app)
        self.user_class = user_class
        self.keys = keys
        self.auth_header = Settings().auth_header or "Authorization"
        self.value_prefix = Settings().value_prefix or "Bearer "

    async def dispatch(self, request: Request, call_next):
        try:
            header_value = request.headers.get(self.auth_header)
            if header_value is None:
                raise Exception("No se encontró el header de autorización")
            if not header_value.startswith(self.value_prefix):
                raise Exception(
                    "El valor del header de autorización no tiene el prefijo correcto"
                )
            token = header_value.replace(self.value_prefix, "").strip()

            if not self.keys:
                raise Exception("No keys provided to locate user")
            attr_name = self.keys[0]
            attr = getattr(self.user_class, attr_name)
            stmt = select(self.user_class).where(attr == token)

            async with AsyncSession(engine) as session:
                result = await session.execute(stmt)
                user = result.scalars().first()
                request.state.user = user
        except Exception as e:
            logger.error(f"Error en UserInRequestSessionMiddleware: {e}")
            raise e
        response = await call_next(request)
        return response


class UserInRequestMiddleware(BaseHTTPMiddleware):
    """Simple middleware that validates the Authorization header and stores the token.
    It does not perform a DB lookup.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.auth_header = Settings().auth_header or "Authorization"
        self.value_prefix = Settings().value_prefix or "Bearer "

    async def dispatch(self, request: Request, call_next):
        try:
            header_value = request.headers.get(self.auth_header)
            if header_value is None:
                raise Exception("No se encontró el header de autorización")
            if not header_value.startswith(self.value_prefix):
                raise Exception(
                    "El valor del header de autorización no tiene el prefijo correcto"
                )
            token = header_value.replace(self.value_prefix, "").strip()
            request.state.token = token
        except Exception as e:
            logger.error(f"Error en UserInRequestMiddleware: {e}")
            raise e
        response = await call_next(request)
        return response
