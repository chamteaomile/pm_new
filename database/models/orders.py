from typing import Set

from .base_model import BaseModel
from .db import db


class Order(BaseModel):
    __tablename__ = 'orders'

    telegram_id = db.Column(db.String(), nullable=True, comment='User Telegram ID')
    ordered_item = db.Column(db.String(), nullable=False, default='', server_default='', comment='Ordered Item Name RU')
    status = db.Column(db.String(), nullable=False, default='', server_default='', comment='Order Status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._applications = set()

    @property
    def applications(self) -> Set:
        return self._applications

    @applications.setter
    def add_application(self, application):
        self._applications.add(application)
