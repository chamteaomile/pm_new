from typing import Set

from datetime import datetime
from sqlalchemy.sql import func
from .base_model import BaseModel
from .db import db


class Item(BaseModel):
    __tablename__ = 'items'

    item_name = db.Column(db.String(), nullable=False, default='', server_default='', comment='Item Name')
    item_category = db.Column(db.String(), nullable=False, default='', server_default='', comment='Category Name')
    item_subcategory = db.Column(db.String(), nullable=False, default='', server_default='', comment='Subcategory Name')
    item_time_quantity = db.Column(db.String(), nullable=False, default='', server_default='', comment='Time Quantity')
    item_time_description = db.Column(db.String(), nullable=False, default='', server_default='',
                                      comment='Time Description')
    item_price = db.Column(db.String(), nullable=False, default='', server_default='', comment='Item Price')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._applications = set()

    @property
    def applications(self) -> Set:
        return self._applications

    @applications.setter
    def add_application(self, application):
        self._applications.add(application)
