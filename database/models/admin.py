from .base_model import BaseModel
from .db import db


class Admin(BaseModel):
    __tablename__ = 'admins'

    role = 'admin'

    telegram_id = db.Column(db.String(), nullable=False, comment='Admin Telegram ID')
    name = db.Column(db.String(), nullable=False, default='', server_default='', comment='Admin name')
