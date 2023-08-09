import datetime

from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Integer, Text, Double
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class Product(Base):
    __tablename__ = 'product'

    id = Column(UUID, primary_key=True)
    image_link = Column(String(255))
    name = Column(String(255))
    description = Column(Text)
    price = Column(Double)
    revision = Column(BigInteger)
    group_id = Column(UUID, ForeignKey('product_group.id'))

    group = relationship('Group', backref='products')
