import traceback
import json
import base64
import hashlib
from functools import singledispatch
from json import JSONDecodeError
from typing import TypeVar, Type, Any
from uuid import UUID

from jwt import JWT, AbstractJWKBase
from jwt.jwk import jwk_from_dict
from pydantic import BaseModel

from server.core.config import CoreSettings
from cryptography.fernet import Fernet, MultiFernet
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = CoreSettings()


# Derivamos una clave determinista a partir del secret_key de la configuración
# para que los tokens sean persistentes entre reinicios del servidor.
def _derive_fernet_key(secret: str, salt: str = "auth_salt") -> bytes:
    key = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), 100000)
    return base64.urlsafe_b64encode(key[:32])


_persistent_key = _derive_fernet_key(settings.secret_key)


class FernetJWK(AbstractJWKBase):
    def __init__(self, key: bytes, kid: str = "default"):
        self._fernet = Fernet(key if isinstance(key, str) else key)
        self._kid = kid

    def get_kty(self) -> str:
        return "oct"

    def get_kid(self) -> str: #TODO: preparar la rotacion de keys[]
        return self._kid

    def is_sign_key(self) -> bool: #TODO: definir cuales son para encript o para sign
        return True

    def sign(self, message: bytes, **options) -> bytes:
        # En este contexto, usamos Fernet para encriptar el contenido
        # Me parece que no entendio que hace este metodo
        return self._fernet.encrypt(message)

    def verify(self, message: bytes, signature: bytes, **options) -> bool:
        # Encriptación simétrica: verificar es intentar desencriptar
        # Me parece que no entendio que hace este metodo 2
        try:
            self._fernet.decrypt(signature)
            return True
        except Exception:
            return False

    def decrypt(self, token: bytes) -> bytes:
        # Me parece que no entendio que hace este metodo 3
        return self._fernet.decrypt(token)

    def to_dict(self, public_only: bool = True) -> dict[str, str]:
        # WTF
        return {"kty": "oct", "kid": self._kid}

    @classmethod
    def from_dict(cls, dct: dict[str, object]) -> "FernetJWK":
        # A este punto no se para que voy a hacer esto
        return cls(key=str(dct["k"]), kid=str(dct.get("kid", "default")))


_jwt = JWT()
_jwk = FernetJWK(_persistent_key) #TODO: implementar esto y arreglarlo

encoder_f = MultiFernet(
    fernets=[Fernet(_persistent_key)]
) #TODO: arreglar la clase de MultiFernet para que la encriptacion rote

user_data_template = {
    "uid": "",
    "iat": 0,
    "exp": 0,
    "iss": "fastapi-module",
    "sub": "auth",
}


@singledispatch
def encode(data: object) -> bytes:
    try:
        if isinstance(data, BaseModel):
            text = data.model_dump_json()
        else:
            text = json.dumps(data, default=lambda o: o.__dict__, sort_keys=True)
    except TypeError:
        text = str(data)
    return encoder_f.encrypt(text.encode("utf-8"))


@encode.register
def _(data: str) -> bytes:
    return encoder_f.encrypt(data.encode("utf-8"))


@encode.register
def _(data: UUID) -> bytes:
    return encoder_f.encrypt(str(data).encode("utf-8"))


@encode.register
def _(data: BaseModel) -> bytes:
    return encoder_f.encrypt(data.model_dump_json().encode("utf-8"))


@encode.register
def _(data: dict) -> bytes:
    text = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return encoder_f.encrypt(text)


T = TypeVar("T")


def decode(data: bytes, dtype: Type[T] | None = None) -> T | Any:
    try:
        plaintext: bytes = encoder_f.decrypt(data)
    except Exception as e:
        logger.error(f"Error decodificando: {e}")
        raise ValueError("Token inválido o expirado") from e

    text = plaintext.decode("utf-8")

    try:
        obj = json.loads(text)
    except JSONDecodeError:
        obj = text

    if dtype is None:
        return obj

    if isinstance(dtype, type) and issubclass(dtype, BaseModel):
        return dtype.model_validate(obj)

    return dtype(obj)


async def get_token(data: dict) -> str:
    """
    Genera un JWT cuyo contenido (payload) está encriptado.
    """
    try:
        # Encriptamos el contenido real
        encrypted_content = encode(data).decode("utf-8")

        # El payload del JWT solo contiene el dato encriptado
        jwt_payload = {
            "pld": encrypted_content,
            "iss": user_data_template["iss"],
            "sub": user_data_template["sub"],
        }

        # Firmamos el JWT (usando el secret_key como llave oct)

        signing_key = jwk_from_dict(
            {
                "kty": "oct",
                "k": base64.urlsafe_b64encode(
                    settings.secret_key.encode()[:32]
                ).decode(),
            }
        )

        return _jwt.encode(jwt_payload, signing_key, alg=settings.jwt_algorithm)
    except Exception as e:
        logger.error(f"Error generando token: {e}")
        logger.error(traceback.format_exc())
        raise


async def read_token(token: str) -> dict:
    """
    Lee un JWT, verifica su firma y desencripta su contenido.
    """
    try:

        verifying_key = jwk_from_dict(
            {
                "kty": "oct",
                "k": base64.urlsafe_b64encode(
                    settings.secret_key.encode()[:32]
                ).decode(),
            }
        )

        # Verificamos y decodificamos el JWT
        claims = _jwt.decode(token, verifying_key, algorithms=[settings.jwt_algorithm])

        # Extraemos y desencriptamos el contenido real
        encrypted_pld: bytes | str | None = claims.get("pld")
        if not encrypted_pld:
            raise ValueError("Token no contiene contenido encriptado")

        decrypted_data = decode(
            encrypted_pld.encode("utf-8") if isinstance(encrypted_pld, str) else encrypted_pld
        )
        return decrypted_data
    except Exception as e:
        logger.error(f"Error leyendo token: {e}")
        logger.error(traceback.format_exc())
        raise ValueError("Token inválido") from e
