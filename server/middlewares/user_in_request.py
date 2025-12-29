from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from server.core.models.base import BaseUser #cambialo al modelo que crees
from server.core.utils.logger import get_logger
from server.config import Settings

logger = get_logger(__name__)

class UserInRequestMiddleware(BaseHTTPMiddleware):
    def __init__(self):
        super().__init__(self)
        self.auth_header = "Authorization" if Settings().auth_header is None else Settings().auth_header
        self.value_prefix = "Bearer " if Settings().value_prefix is None else Settings().value_prefix

    async def dispatch(self, request: Request, call_next):
        try:
            headers = request.headers.get(self.auth_header)
            if headers is None:
                raise Exception("No se encontró el header de autorización")
            if not headers.startswith(self.value_prefix):
                raise Exception("El valor del header de autorización no tiene el prefijo correcto")
            token = headers.replace(self.value_prefix, "")
        except Exception as e:
            logger.error(f"Error en UserInRequestMiddleware: {e}")
            raise e