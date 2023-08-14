import datetime

from sqlalchemy import Column, BigInteger, DateTime, String, UUID, ForeignKey, Integer, select, delete
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tgbot.services.database.base import Base


class Cart(Base):
    __tablename__ = 'cart'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    iiko_user_id = Column(UUID, ForeignKey('iiko_user.id'))
    product_id = Column(UUID, ForeignKey('product.id'))
    quantity = Column(Integer, default=1)

    product = relationship('Product')
    iiko_user = relationship('IikoUser', backref='cart_products')

    @classmethod
    async def clear_old_products(cls, session, user_id, revision):
        stmt = delete(Cart).where(Cart.iiko_user_id == user_id, Cart.product.revision != revision)
        await session.execute(stmt)

    @classmethod
    async def get_user_product(cls, session, user_id, product_id):
        stmt = select(Cart).where(Cart.iiko_user_id == user_id, Cart.product_id == product_id)
        record = await session.execute(stmt)

        return record.scalar()
