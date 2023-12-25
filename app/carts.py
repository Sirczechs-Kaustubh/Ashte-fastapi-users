from app.db import *
from app.users import current_active_user, current_superuser
from fastapi.background import BackgroundTasks
from emails import order_success_email
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas import OrderEdit

carts_router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)
checkout_router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
    )
orders_router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
    )

# show the cart
@carts_router.get("/show")
async def get_cart(db: AsyncSession = Depends(get_async_session),
                    user: User = Depends(current_active_user)):
    cart = await session.query(Cart).filter(Cart.user_id == user.id).order_by(Cart.id.desc()).first()  # Retrieve latest cart
    if cart is None:
        raise HTTPException(404, "No cart found for the user")

    cart_items = cart.items  # Retrieve cart items
    return {"cart_items": cart_items, "cart_id": cart.id}

# in the frontend temporarily store the cart items and when user clicks on
# confirm cart add the cart items to the cart using add route.
# Add items to cart
@carts_router.post("/add")
async def add_to_cart(
    product_ids: List[int],  # Accept multiple product IDs
    quantities: List[int],  # Accept corresponding quantities
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    cart = await db.get(Cart, user_id=user.id)
    if not cart:
        cart = Cart(user_id=user.id)  # Create a new cart if it doesn't exist
        db.add(cart)

    for product_id, quantity in zip(product_ids, quantities):
        product = await db.get(Product, product_id)

        # Ensure sufficient product quantity
        if quantity > product.quantity:
            raise HTTPException(400, f"Not enough stock for product {product_id}")

        existing_item = await db.get(CartItem, cart_id=cart.id, product_id=product_id)
        if existing_item:
            existing_item.quantity += quantity  # Update existing item quantity
        else:
            cart_item = CartItem(product=product, quantity=quantity, cart=cart)
            db.add(cart_item)

        # Reduce product quantity
        product.quantity -= quantity
        db.add(product)  # Re-add product to update its quantity

    await db.commit()
    return {"message": "Products added to cart"}


# Please send the cart-id for this function after getting it from show cart
@carts_router.delete("/remove/{item_id}")
async def remove_from_cart(
    item_id: int,
    cart_id: int = Body(...),  # Accept Cart.id from frontend
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    cart_item = await session.get(CartItem, item_id)

    # Ensure the item belongs to the specified cart and the user has access
    if cart_item.cart_id == cart_id and cart_item.cart.user_id == user.id:
        product = cart_item.product  # Retrieve the associated product
        product.quantity += cart_item.quantity  # Restock the product quantity
        session.delete(cart_item)  # Delete the cart item
        await session.commit()  # Commit the changes to the database
        return {"message": "Item removed from cart"}
    else:
        raise HTTPException(403, "Unauthorized to remove item")

@carts_router.get("/summary")
async def get_cart_summary(
    cart_id: int,  # Accept Cart.id as path parameter
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    cart = await session.get(Cart, cart_id)

    # Ensure the user has access to the specified cart
    if cart.user_id != user.id:
        raise HTTPException(403, "Unauthorized to access this cart")

    total_quantity = sum(item.quantity for item in cart.items)
    total_price = sum(item.product.price * item.quantity for item in cart.items)
    return {"total_quantity": total_quantity, "total_price": total_price}


@checkout_router.post("/")
async def create_checkout(
    cart_id: int = Body(...),  # Receive Cart.id from frontend
    user: User = Depends(current_active_user),
    amount: float = Body(...),  # Receive amount from frontend
    email: str = Body(...),  # Receive other checkout details
    name: str = Body(...),
    phone_no: int = Body(...),
    address: str = Body(...),
    postal_code: str = Body(...),
    db: AsyncSession = Depends(get_async_session),
):
    cart = await session.get(Cart, cart_id)  # Fetch the specified cart

    # Ensure the user has access to the cart
    if cart.user_id != user.id:
        raise HTTPException(403, "Unauthorized to checkout this cart")

    checkout = Checkout(
        user_id=user.id,
        cart_id=cart.id,  # Use the provided cart_id
        email=email,
        name=name,
        phone_no=phone_no,
        address=address,
        postal_code=postal_code,
        amount=amount,
    )
    db.add(checkout)
    await db.commit()

    return {"message": "Checkout successful"}

# Make sure to pass the cart_id as well from the frontend
@orders_router.post("/create")
async def create_order(
    cart_id: int = Body(...),  # Receive Cart.id from frontend
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    cart = await session.get(Cart, cart_id)  # Fetch the specified cart

    # Ensure the user has access to the cart
    if cart.user_id != user.id:
        raise HTTPException(403, "Unauthorized to create order from this cart")

    # Retrieve products from the cart
    products = list(cart.items.values())

    order = Orders(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        user_address=user.address,
        paid=True,  # Mark as paid immediately
        cart_id=cart_id,
        products=products
    )
    db.add(order)
    await db.commit()
    order_id = order.id
    #################################################################
    # Payment successful and order placed mail I need to implements #
    #################################################################
    background_tasks.add_task(order_success_email, user.email,token)
    return {"message": "Order created and marked as paid successfully"}

@orders_router.post("/view")
async def view_order(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    try:
        if user.is_superuser:
            orders = await db.query(Orders).filter(Orders.shipped == False).all()
        else:
            orders = await db.query(Orders).filter(
                Orders.user_id == user.id
            ).all()

        return {"orders": orders}  # Return orders in a structured response

    except IntegrityError as e:
        raise HTTPException(
            status_code=409, detail="Database integrity error: {}".format(str(e))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

    return orders

@orders_router.put("/edit/{order_id}")
async def edit_order(
    order_id: int,
    user: User = Depends(current_superuser),
    data: OrderEdit = Body(...),  # Receive updated field values
    db: AsyncSession = Depends(get_async_session)
):
    if not user.is_superuser:
        raise HTTPException(403, "Unauthorized to edit orders")

    order = await db.get(Orders, order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    # Update the specified fields based on the received data
    if data.shipped is not None:
        order.shipped = data.shipped
    if data.paid is not None:
        order.paid = data.paid

    db.add(order)
    await db.commit()

    return {"message": "Order updated successfully"}

