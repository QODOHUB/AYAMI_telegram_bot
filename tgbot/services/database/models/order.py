import datetime

from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Integer, Double, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class OrderProduct(Base):
    __tablename__ = 'order_product'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(UUID, ForeignKey('order.id'))
    product_id = Column(UUID, ForeignKey('product.id'))
    final_price = Column(Double)
    quantity = Column(Integer)

    product = relationship('Product', lazy='selectin')


class Order(Base):
    __tablename__ = 'order'

    id = Column(UUID, primary_key=True)
    iiko_user_id = Column(UUID, ForeignKey('iiko_user.id'))
    payment_sum = Column(Double)
    created_at = Column(DateTime(), default=datetime.datetime.now())

    iiko_user = relationship('IikoUser', backref='orders')
    products = relationship('OrderProduct', backref='order')
