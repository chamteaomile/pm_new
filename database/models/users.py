from typing import Set

from .base_model import BaseModel
from .db import db


class User(BaseModel):
    __tablename__ = 'users'

    name = db.Column(db.String(), nullable=False, default='', server_default='', comment='User Name')
    phone_number = db.Column(db.String(), nullable=False, default='', server_default='', comment='User Phone Number')
    telegram_id = db.Column(db.String(), nullable=True, comment='Telegram ID')
    weight = db.Column(db.String(), nullable=False, default='', server_default='', comment='User Weight')
    height = db.Column(db.String(), nullable=False, default='', server_default='', comment='User Height')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._applications = set()

    @property
    def applications(self) -> Set:
        return self._applications

    @applications.setter
    def add_application(self, application):
        self._applications.add(application)
