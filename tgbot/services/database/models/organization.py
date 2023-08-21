from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Integer, Double, Table, Boolean, select
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class Organization(Base):
    __tablename__ = 'organization'

    id = Column(UUID, primary_key=True)
    name = Column(String(255))
    code = Column(String(32))
    address = Column(String(255))
    name_in_bot = Column(String(64))
    show_in_bot = Column(Boolean, default=False)

    @classmethod
    async def get_all(cls, session):
        stmt = select(Organization).where(Organization.show_in_bot == True)
        records = await session.execute(stmt)
        result = records.scalars().all()

        return result
