import uuid
from fastapi_users import schemas
from typing import Optional
from pydantic import BaseModel
from datetime import date



class UserBase(BaseModel):
    first_name:str
    last_name:str
    
class UserRead(UserBase,schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(UserBase,schemas.BaseUserCreate):
    pass


class UserUpdate(UserBase,schemas.BaseUserUpdate):
    pass

class ProductCreate(BaseModel):
    title: str
    description: str
    price: float
    release_date: Optional[date]
    quantity: int
    is_visible: Optional[bool] = False


class ProductUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    price: Optional[float]
    release_date: Optional[date]
    quantity: Optional[int]
    is_visible: Optional[bool]

class OrderEdit(BaseModel):
    shipped: Optional[bool]
    paid : Optional[bool]
