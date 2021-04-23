import sys
import uuid
from base64 import b64encode
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict

from ddtrace import tracer
from gino.crud import CRUDModel as _CRUDModel
from gino.dialects.asyncpg import AsyncpgDialect
from gino.dialects.asyncpg import DBAPICursor as _DBAPICursor
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator


if 'sanic' in sys.modules:
    from gino.ext.sanic import Gino as _Gino
else:
    from gino import Gino as _Gino


class DBAPICursor(_DBAPICursor):
    async def async_execute(self, query, timeout, args, limit=0, many=False):
        with tracer.trace('postgres.query', service='postgres') as span:
            span.set_tag('query', query)
            span.set_tag('args', [str(arg)[:100] for arg in args])
            result = await super().async_execute(query, timeout, args, limit=0, many=False)
        return result


AsyncpgDialect.cursor_cls = DBAPICursor


class NDArray(TypeDecorator):
    impl = postgresql.BYTEA


class CRUDModel(_CRUDModel):
    __hiden_keys__ = ()

    def to_dict(self, del_hiden_keys: bool = True) -> Dict:
        data = {}
        for key in list(self.__dict__.get('__values__', {}).keys()) + list(self.__dict__.keys()):
            if key.startswith('_') or (del_hiden_keys and key in getattr(self, '__hiden_keys__', [])):
                continue
            value = getattr(self, key, None)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, datetime):
                value = value.isoformat(' ')
            elif isinstance(value, timedelta):
                value = value.total_seconds()
            elif isinstance(value, Enum):
                value = value.value
            elif isinstance(value, bytes):
                value = b64encode(value).decode()
            elif isinstance(value, _CRUDModel):
                value = value.to_dict()
            data[key] = value
        return data


class Gino(_Gino):
    model_base_classes = (CRUDModel,)
    NDArray = NDArray


db = Gino()
