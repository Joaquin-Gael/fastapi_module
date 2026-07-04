import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from rich.logging import RichHandler

from core.config import settings

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

_KV_PATTERN = re.compile(
    r"(?i)(password|passwd|pwd|secret|token|access[_-]?token|refresh[_-]?token|authorization|api[_-]?key|sessionid|cookie|set[_-]?cookie)"
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
        return _KV_PATTERN.sub(lambda m: f"{m.group(1)}=" + "*"*5, text)

    def _redact_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        redacted: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in _SENSITIVE_KEYS:
                redacted[k] = "*"*5
            else:
                if isinstance(v, str):
                    redacted[k] = self._redact_str(v)
                else:
                    redacted[k] = v
        return redacted

    def filter(self, record: logging.LogRecord) -> bool:
        if self.debug:
            return True

        if isinstance(record.msg, str):
            record.msg = self._redact_str(record.msg)

        if isinstance(record.args, dict):
            record.args = self._redact_mapping(record.args)
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

        for key in list(record.__dict__.keys()):
            if isinstance(key, str) and key.lower() in _SENSITIVE_KEYS:
                record.__dict__[key] = "*"*5

        return True


class TZFormatter(logging.Formatter):
    """
    Formatter que incluye hora con zona (UTC por defecto), archivo y línea:
    Ejemplo: 2025-12-27T12:34:56Z | INFO | server/core/x.py:123 | mensaje
    """

    def __init__(self, *, tz: timezone = timezone.utc) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d/%H:%M:%S",
        )
        self.tz = tz

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=self.tz)
        base = dt.strftime(datefmt or "%Y-%m-%dT%H:%M:%S")
        # Sufijo Z para indicar UTC; si quieres local, ajusta self.tz
        return f"{base}Z" if self.tz == timezone.utc else base


class RedisHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            from ..tasks.base.task_save_logs import rsave_log, save_log

            log_data = {
                "meta": getattr(record, "meta", {}),
                "type": record.levelname,
                "level": getattr(record, "loglevel", None),
                "status": getattr(record, "status", None),
                "action": getattr(record, "action", None),
                "assistant_message": getattr(record, "assistant_message", "N/A"),
                "source": getattr(record, "source", "N/A"),
                "final_message": self.format(record),
            }

            rsave_log.delay(log_data)
            save_log.delay(log_data)

        except Exception as e:
            print(f"Error al guardar log en redis: {e}")
            self.handleError(record)


_configured = False


def _get_debug() -> bool:
    """
    Determina el modo DEBUG, primero intentando Settings(), luego variable de entorno DEBUG.
    """
    if settings is not None:
        try:
            return bool(settings.debug)
        except Exception:
            pass

    val = os.getenv("DEBUG", "false").strip().lower()
    return val in ("1", "true", "yes", "on")


def _get_celery_logger(name: str | None = None) -> logging.Logger:
    logger_name = name or "celery"
    logger = logging.getLogger(logger_name)
    debug = _get_debug()
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_level=True,
        show_path=False,
    )
    console_handler.setLevel(level)
    console_handler.setFormatter(TZFormatter(tz=settings.timezone))
    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger



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
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,  # lo manejamos con nuestro Formatter
        show_level=True,
        show_path=False,  # usamos filename:lineno del Formatter
    )
    console_handler.setLevel(level)
    console_handler.setFormatter(TZFormatter(tz=settings.timezone))
    console_handler.addFilter(SensitiveDataFilter(debug=debug))

    logging.root.handlers.clear()
    logging.root.addHandler(console_handler)

    _configured = True


logging.getLogger("multipart").setLevel(logging.INFO)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Obtiene un logger con la configuración estandarizada.
    - name: nombre del logger (por defecto del módulo que lo llama).
    """
    configure_logging()

    debug = _get_debug()

    level = logging.DEBUG if debug else logging.INFO

    redis_handler = RedisHandler()
    redis_handler.setLevel(level)
    redis_handler.setFormatter(TZFormatter(tz=settings.timezone))
    redis_handler.addFilter(SensitiveDataFilter(debug=debug))

    log_file = settings.log_file or Path(__file__).parent.parent.joinpath(
        "data/server.log"
    )
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(TZFormatter(tz=settings.timezone))
    file_handler.addFilter(SensitiveDataFilter(debug=debug))

    logging.root.addHandler(file_handler)

    logger = logging.getLogger(name or __name__)
    logger.addHandler(redis_handler)
    return logger
