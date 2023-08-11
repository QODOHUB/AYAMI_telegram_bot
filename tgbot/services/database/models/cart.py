import datetime

from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class Cart(Base):
    __tablename__ = 'cart'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    iiko_user_id = Column(UUID, ForeignKey('iiko_user.id'))
    product_id = Column(UUID, ForeignKey('product.id'))
    quantity = Column(Integer, default=1)

    iiko_user = relationship('IikoUser', backref='cart')
