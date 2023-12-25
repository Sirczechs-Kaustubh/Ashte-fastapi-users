from fastapi import APIRouter

from app.db import *
from sqlalchemy.orm import Session
from sqlalchemy.future import select  # Add this import
from app.schemas import ProductCreate, ProductUpdate
from app.users import current_active_user

products_router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

@products_router.get("/")
async def get_all_products(db: Session = Depends(get_async_session)):
    try:
        result = await db.execute(select(Product).filter(Product.is_visible == True).limit(20))
        products = result.scalars().all()
        return products
    # check for the quantity of products and display out of stock message
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e

@products_router.post("/add")
async def create_product(
    *,
    db: Session = Depends(get_async_session),
    user: User = Depends(current_active_user),
    product_data: ProductCreate,
):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    product = Product(**product_data.dict())  
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@products_router.patch("/{product_id}")
async def update_product(*,
                         product_id: int,
                         db: Session = Depends(get_async_session),
                         user: User = Depends(current_active_user),
                         product_data: ProductUpdate = Depends()):  # Add Depends() here
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.execute(select(Product).filter_by(id=product_id))
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Assuming Product model has an update method
    product.update(**product_data.dict())
    await db.commit()
    return product


@products_router.delete("/{product_id}")
async def delete_product(*,
                         product_id: int,
                         db: Session = Depends(get_async_session),
                         user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(Product).filter_by(id=product_id))
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}

    

    
    

    

    
