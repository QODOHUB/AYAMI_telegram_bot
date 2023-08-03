import datetime

from sqlalchemy import Column, BigInteger, DateTime, String
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class TelegramUser(Base):
    __tablename__ = 'telegram_user'

    telegram_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    created_at = Column(DateTime(), default=datetime.datetime.now(), nullable=False)
    mention = Column(String(64))
    full_name = Column(String(64))
