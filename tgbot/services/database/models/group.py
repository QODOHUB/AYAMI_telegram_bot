import datetime

from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Integer, select, Boolean
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
    image_in_bot = Column(String(255))
    show_in_bot = Column(Boolean, default=False)

    parent = relationship('Group', lazy='selectin', backref='children', remote_side='Group.id')

    @classmethod
    async def get_main_groups(cls, session, revision: int):
        stmt = select(Group).where(Group.parent_id == None, Group.revision == revision, Group.show_in_bot == True)
        records = await session.execute(stmt)

        return records.scalars().all()
