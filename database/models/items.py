from typing import Set

from datetime import datetime
from sqlalchemy.sql import func
from .base_model import BaseModel
from .db import db


class Item(BaseModel):
    __tablename__ = 'items'

    data = db.Column(db.String(), nullable=False, default='', server_default='', comment='Item ENG Name')
    name = db.Column(db.String(), nullable=False, default='', server_default='', comment='Item RU Name')
    price = db.Column(db.String(), nullable=False, default='', server_default='', comment='Item Price')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._applications = set()

    @property
    def applications(self) -> Set:
        return self._applications

    @applications.setter
    def add_application(self, application):
        self._applications.add(application)
