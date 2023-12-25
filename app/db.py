from typing import AsyncGenerator
from sqlalchemy import (Column,String,Integer,Float,Date, func,Boolean
                        , ForeignKey, Table)
import enum

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship


DATABASE_URL = "sqlite+aiosqlite:///./test.db"



class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    cart = relationship('Cart', uselist=False, backref='user')
    checkout = relationship('Checkout', uselist=False, backref='user')
    orders = relationship('Orders', backref='user')

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(Float, nullable=False)
    release_date = Column(Date)
    quantity = Column(Integer, nullable=True)
    is_visible = Column(Boolean, default=False)
    created_date = Column(Date,default=func.current_date())
    updated_date = Column(Date,default=func.current_date(),onupdate=func.current_date())

class Cart(Base):
    __tablename__ = 'carts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))  # Link to User model
    user = relationship('User', backref ='carts')
    items = relationship('CartItem', back_populates='cart')
    checkout = relationship('Checkout', uselist=False, backref='carts')

class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id'))
    product_id = Column(Integer, ForeignKey('products.id'))  # Link to Product model
    quantity = Column(Integer)
    cart = relationship('Cart', backref='items')
    product = relationship('Product')
    
class Checkout(Base):
    __tablename__ = 'checkouts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    cart_id = Column(Integer, ForeignKey('carts.id'))
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone_no = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    amount=Column(Float,nullable=False)
    user = relationship('User', backref='checkout')
    cart = relationship('Cart', backref='checkout')

class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user_name = Column(String, nullable=False)
    user_email = Column(String, nullable=False)
    user_address = Column(String, nullable=False)
    paid = Column(Boolean, default=False)
    shipped = Column(Boolean, default=False)
    products = relationship('Product', secondary='order_products')
    cart_id = Column(Integer, ForeignKey('carts.id'))
    
order_products = Table(
    'order_products',
    Base.metadata,
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('product_id', Integer, ForeignKey('products.id'))
)



engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)



