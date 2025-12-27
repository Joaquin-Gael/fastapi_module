from pydantic import BaseModel, Field
from typing import Optional

class FormBase(BaseModel):
    limit: Optional[int] = Field(default=None)
    pages: Optional[int] = Field(default=None)
    offset: Optional[int] = Field(default=None)
    fields: Optional[list[str]] = Field(default=None, description="campos del modelo a retornar en la respuesta serializada")
    page: Optional[int] = Field(default=None, description="pagina a retornar")