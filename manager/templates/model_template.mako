from sqlmodel import Field
from server.core.models.base.main import BaseSQLModel
<%
    has_datetime = any(f.get('type') == 'datetime' or f.get('type') == 'date' for f in fields.values())
    has_uuid = any(f.get('type') == 'UUID' for f in fields.values())
    has_nullable = any(f.get('nullable', True) for f in fields.values())
%>\
% if has_datetime:
from datetime import datetime, timezone
% endif
% if has_uuid:
from uuid import UUID, uuid4
% endif
% if has_nullable:
from typing import Optional
% endif


class ${model_name}(BaseSQLModel, table=True):
    __tablename__ = "${table_name}s"
    __table_args__ = {"extend_existing": True}

% for field_name, field_data in fields.items():
<%
    ftype = field_data.get('type', 'str')
    nullable = field_data.get('nullable', True)
    primary_key = field_data.get('primary_key', False)
    unique = field_data.get('unique', False)
    index = field_data.get('index', False)
    default = field_data.get('default', None)
    max_length = field_data.get('max_length', 255)

    # Build Field() kwargs
    kwargs = []
    if max_length and ftype == 'str':
        kwargs.append(f"max_length={max_length}")
    if not nullable:
        kwargs.append("nullable=False")
    if nullable:
        kwargs.append("nullable=True")
    if primary_key:
        kwargs.append("primary_key=True")
    if unique:
        kwargs.append("unique=True")
    if index:
        kwargs.append("index=True")
    if default is not None:
        if ftype == 'bool':
            kwargs.append(f"default={str(default)}")
        elif ftype == 'int' or ftype == 'float':
            kwargs.append(f"default={default}")
        elif ftype == 'datetime' and default == 'utcnow':
            kwargs.append("default_factory=lambda: datetime.now(timezone.utc)")
        elif ftype == 'UUID':
            kwargs.append("default_factory=uuid4")
        else:
            kwargs.append(f"default={repr(default)}")

    # Python type annotation
    py_type_map = {
        'str': 'str',
        'int': 'int',
        'float': 'float',
        'bool': 'bool',
        'datetime': 'datetime',
        'date': 'datetime',
        'UUID': 'UUID',
    }
    py_type = py_type_map.get(ftype, 'str')
    if nullable and ftype not in ('UUID',):
        py_type = f"Optional[{py_type}]"
%>\
    ${field_name}: ${py_type} = Field(${', '.join(kwargs)})
% endfor
