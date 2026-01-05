from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional

class FormBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        serialize_by_alias=True,
        populate_by_name=True
    )
    pass

class SimpleForm(FormBase):
    pass

class FilterForm(FormBase):
    limit: Optional[int] = Field(default=None)
    pages: Optional[int] = Field(default=None)
    offset: Optional[int] = Field(default=None)
    fields: Optional[list[str]] = Field(default=None, description="campos del modelo a retornar en la respuesta serializada")
    page: Optional[int] = Field(default=None, description="pagina a retornar")