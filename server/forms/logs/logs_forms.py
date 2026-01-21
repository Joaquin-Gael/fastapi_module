from typing import Optional

from pydantic import Field

from server.forms.base import FilterForm


class LogsFilterForm(FilterForm):
    word_key: Optional[str] = Field(
        default=None, description="palabra clave a buscar en los logs"
    )
    pass
