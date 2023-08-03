from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Date, Integer, select
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class IikoUser(Base):
    __tablename__ = 'iiko_user'

    id = Column(UUID, primary_key=True, autoincrement=False)
    referrer_id = Column(UUID, ForeignKey('iiko_user.id'))
    telegram_id = Column(BigInteger, ForeignKey('telegram_user.telegram_id'), unique=True)
    name = Column(String(64))
    surname = Column(String(64))
    middle_name = Column(String(64))
    comment = Column(String(128))
    phone = Column(String(20), unique=True)
    culture_name = Column(String(64))
    birthday = Column(Date)
    email = Column(String(64))
    sex = Column(Integer, default=0)
    bonus_balance = Column(Integer, default=0)

    referrer = relationship('IikoUser')
    telegram_user = relationship('TelegramUser', backref='iiko_user', uselist=False)

    @classmethod
    async def get_by_phone(cls, session, phone):
        stmt = select(IikoUser).where(IikoUser.phone == phone)
        record = await session.execute(stmt)
        iiko_user = record.scalar()

        return iiko_user
