import datetime

from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Integer, select
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base
from tgbot.services.iiko.api import Iiko


class Group(Base):
    __tablename__ = 'product_group'

    id = Column(UUID, primary_key=True)
    image_link = Column(String(255))
    name = Column(String(128))
    revision = Column(BigInteger)
    parent_id = Column(UUID, ForeignKey('product_group.id'), nullable=True)

    parent = relationship('Group', lazy='selectin', backref='children', remote_side='Group.id')

    @classmethod
    async def get_main_groups(cls, session):
        stmt = select(Group).where(Group.parent_id == None)
        records = await session.execute(stmt)

        return records.scalars().all()