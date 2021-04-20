from datetime import datetime
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .db import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(UUID(), primary_key=True, default=uuid4, server_default=func.uuid_generate_v4(), comment='ID')
    create_datetime = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, server_default=func.now(),
                                comment='UTC create datetime')
    update_datetime = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, server_default=func.now(),
                                comment='UTC update datetime')
