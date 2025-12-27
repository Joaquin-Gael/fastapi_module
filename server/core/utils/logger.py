# Este módulo define un logger centralizado con:
# - Formato con hora exacta y archivo/linea de origen
# - Redacción de datos sensibles cuando DEBUG está desactivado
#
# Úsalo así:
#   from server.core.utils.logger import get_logger
#   log = get_logger(__name__)
#   log.info("mensaje")
#
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict
from datetime import datetime, timezone

from rich.logging import RichHandler

try:
    # Si existe configuración tipada, la usamos para leer DEBUG
    from server.config import Settings  # type: ignore
except Exception:
    Settings = None  # fallback


# Claves que consideramos sensibles para redacción.
_SENSITIVE_KEYS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "apikey",
    "sessionid",
    "cookie",
    "set-cookie",
)

# Patrón para detectar pares clave-valor en mensajes de texto plano.
_KV_PATTERN = re.compile(
    r"(?i)(password|passwd|pwd|secret|token|access_token|refresh_token|authorization|api[_-]?key|sessionid|cookie|set-cookie)"
    r"\\s*[:=]\\s*([^\\s,;]+)"
)


class SensitiveDataFilter(logging.Filter):
    """
    Filtro que elimina o redácta datos sensibles del registro cuando DEBUG está desactivado.

    - Si DEBUG=True: no redácta nada (útil en desarrollo).
    - Si DEBUG=False: redácta claves sensibles en msg, args y extra.
    """

    def __init__(self, debug: bool) -> None:
        super().__init__()
        self.debug = debug

    def _redact_str(self, text: str) -> str:
        # Reemplaza valores sensibles en un string por "***"
        return _KV_PATTERN.sub(lambda m: f"{m.group(1)}=***", text)

    def _redact_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Crea una copia con claves sensibles redáctadas
        redacted: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in _SENSITIVE_KEYS:
                redacted[k] = "***"
            else:
                if isinstance(v, str):
                    redacted[k] = self._redact_str(v)
                else:
                    redacted[k] = v
        return redacted

    def filter(self, record: logging.LogRecord) -> bool:
        if self.debug:
            # En DEBUG no redáctamos para facilitar desarrollo.
            return True

        # Redacción en record.msg si es string
        if isinstance(record.msg, str):
            record.msg = self._redact_str(record.msg)

        # Redacción en record.args si es dict o tupla de strings
        if isinstance(record.args, dict):
            record.args = self._redact_mapping(record.args)  # type: ignore
        elif isinstance(record.args, tuple):
            new_args = []
            for a in record.args:
                if isinstance(a, str):
                    new_args.append(self._redact_str(a))
                elif isinstance(a, dict):
                    new_args.append(self._redact_mapping(a))
                else:
                    new_args.append(a)
            record.args = tuple(new_args)

        # Redacción de atributos extra si existen
        for key in list(record.__dict__.keys()):
            if isinstance(key, str) and key.lower() in _SENSITIVE_KEYS:
                record.__dict__[key] = "***"

        return True


class TZFormatter(logging.Formatter):
    """
    Formatter que incluye hora con zona (UTC por defecto), archivo y línea:
    Ejemplo: 2025-12-27T12:34:56Z | INFO | server/core/x.py:123 | mensaje
    """

    def __init__(self, *, tz: timezone = timezone.utc) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        self.tz = tz

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=self.tz)
        base = dt.strftime(datefmt or "%Y-%m-%dT%H:%M:%S")
        # Sufijo Z para indicar UTC; si quieres local, ajusta self.tz
        return f"{base}Z" if self.tz == timezone.utc else base


_configured = False


def _get_debug() -> bool:
    """
    Determina el modo DEBUG, primero intentando Settings(), luego variable de entorno DEBUG.
    """
    # Intento con Settings tipado
    if Settings is not None:
        try:
            return bool(Settings().debug)
        except Exception:
            pass

    # Fallback a entorno
    val = os.getenv("DEBUG", "false").strip().lower()
    return val in ("1", "true", "yes", "on")


def configure_logging() -> None:
    """
    Configura logging global si aún no está configurado:
    - Nivel según DEBUG (DEBUG vs INFO)
    - RichHandler con timezone en formato, archivo y línea
    - Filtro de datos sensibles
    """
    global _configured
    if _configured:
        return

    debug = _get_debug()

    level = logging.DEBUG if debug else logging.INFO
    logging.captureWarnings(True)
    logging.root.setLevel(level)

    # Handler rico para consola con traceback legible
    handler = RichHandler(
        rich_traceback=True,
        show_time=False,  # lo manejamos con nuestro Formatter
        show_level=True,
        show_path=False,  # usamos filename:lineno del Formatter
    )
    handler.setLevel(level)
    handler.setFormatter(TZFormatter(tz=timezone.utc))

    # Filtro de datos sensibles (activo cuando no hay DEBUG)
    handler.addFilter(SensitiveDataFilter(debug=debug))

    # Limpia handlers previos para evitar duplicados
    logging.root.handlers.clear()
    logging.root.addHandler(handler)

    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Obtiene un logger con la configuración estandarizada.
    - name: nombre del logger (por defecto del módulo que lo llama).
    """
    configure_logging()
    return logging.getLogger(name or __name__)

