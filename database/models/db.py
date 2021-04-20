import sys
import uuid
from base64 import b64encode
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict

import msgpack
import msgpack_numpy
import numpy
from ddtrace import tracer
from gino.crud import CRUDModel as _CRUDModel
from gino.dialects.asyncpg import AsyncpgDialect
from gino.dialects.asyncpg import DBAPICursor as _DBAPICursor
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeDecorator


if 'sanic' in sys.modules:
    from gino.ext.sanic import Gino as _Gino  # pylint: disable=import-error
else:
    from gino import Gino as _Gino


class DBAPICursor(_DBAPICursor):
    async def async_execute(self, query, timeout, args, limit=0, many=False):  # pylint: disable=too-many-arguments
        with tracer.trace('postgres.query', service='postgres') as span:
            span.set_tag('query', query)
            span.set_tag('args', [str(arg)[:100] for arg in args])
            result = await super().async_execute(query, timeout, args, limit=0, many=False)
        return result


AsyncpgDialect.cursor_cls = DBAPICursor


class NDArray(TypeDecorator):  # pylint: disable=abstract-method
    impl = postgresql.BYTEA
    python_type = numpy.ndarray

    def process_bind_param(self, value: numpy.ndarray, dialect: Dialect) -> bytes:
        return msgpack.packb(value, use_bin_type=True)

    def process_result_value(self, value: bytes, dialect: Dialect) -> numpy.ndarray:
        return msgpack.unpackb(value, use_list=False, raw=False)


class CRUDModel(_CRUDModel):
    __hiden_keys__ = ()

    def to_dict(self, del_hiden_keys: bool = True) -> Dict:  # pylint: disable=arguments-differ
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


msgpack_numpy.patch()
db = Gino()
