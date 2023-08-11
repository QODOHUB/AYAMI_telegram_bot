from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Date, Integer, select, Double
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base
from tgbot.services.iiko.schemas import Customer


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
    bonus_balance = Column(Double, default=0)

    referrer = relationship('IikoUser')
    telegram_user = relationship('TelegramUser', backref=backref('iiko_user', uselist=False), uselist=False)

    @classmethod
    async def get_by_phone(cls, session, phone):
        stmt = select(IikoUser).where(IikoUser.phone == phone)
        record = await session.execute(stmt)
        iiko_user = record.scalar()

        return iiko_user

    @classmethod
    async def get_by_telegram_id(cls, session, telegram_id: int):
        stmt = select(IikoUser).where(IikoUser.telegram_id == telegram_id)
        record = await session.execute(stmt)
        iiko_user = record.scalar()

        return iiko_user

    @classmethod
    async def create_or_update_from_api(cls, session, customer: Customer):
        iiko_user: IikoUser = await session.get(IikoUser, customer.id)
        if iiko_user:
            iiko_user.referrer_id = customer.referrerId
            iiko_user.name = customer.name
            iiko_user.surname = customer.surname
            iiko_user.middle_name = customer.middleName
            iiko_user.comment = customer.comment
            iiko_user.culture_name = customer.cultureName
            iiko_user.birthday = customer.birthday
            iiko_user.email = customer.email
            iiko_user.sex = customer.sex
            iiko_user.bonus_balance = customer.walletBalances[0].balance
        else:
            iiko_user = IikoUser(
                id=customer.id,
                referrer_id=customer.referrerId,
                name=customer.name,
                surname=customer.surname,
                middle_name=customer.middleName,
                comment=customer.comment,
                phone=customer.phone.replace('+', ''),
                culture_name=customer.cultureName,
                birthday=customer.birthday,
                email=customer.email,
                sex=customer.sex,
                bonus_balance=customer.walletBalances[0].balance,
            )
            session.add(iiko_user)

        await session.commit()
        return iiko_user
