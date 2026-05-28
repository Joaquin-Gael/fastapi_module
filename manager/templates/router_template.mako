from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

#----------------- EXTRAS ----------------
% if ext_imports
% for lib, deps in ext_imports
<%
    form_deps = ",".join(deps)
%>
from ${lib} import ${form_deps}
% endfor
% endif

from libs.fastapi_crudrouter import SQLModelAsyncCRUDRouter

from core import SessionDep
from core.spi.base.users import SPIBaseUsers, get_session


<%
    router_tag = path_router.title() + "s"
%>

router = APIRouter(prefix="/${path_router}", tags=["${router_tag}"])

crud_router = SQLModelAsyncCRUDRouter(
    schema=#COLOCA ES SCHEMA DE EL MODELO,
    db_model=${spi_name}.${model_name},
    model_id_field="id",
    model_name=${model_name},
    db=get_session,
)