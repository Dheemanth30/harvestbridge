from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_business

router = APIRouter()


def build_product_response(p: models.Product) -> schemas.ProductResponse:
    return schemas.ProductResponse(
        id=p.id, farmer_id=p.farmer_id, name=p.name, category=p.category,
        description=p.description, price_per_unit=p.price_per_unit, unit=p.unit,
        quantity_available=p.quantity_available, min_order_qty=p.min_order_qty,
        is_organic=p.is_organic, image_path=p.image_path, created_at=p.created_at,
        farmer_name=p.farmer.user.name if p.farmer and p.farmer.user else None,
        farm_name=p.farmer.farm_name if p.farmer else None,
        farmer_location=p.farmer.location if p.farmer else None,
        farmer_phone=p.farmer.user.phone if p.farmer and p.farmer.user else None,
    )


def build_cart_response(user_id: int, db: Session) -> schemas.CartResponse:
    items = db.query(models.CartItem).filter(models.CartItem.business_user_id == user_id).all()
    cart_items = []
    total = 0.0
    for item in items:
        subtotal = item.quantity * item.product.price_per_unit
        total += subtotal
        cart_items.append(schemas.CartItemResponse(
            id=item.id, product_id=item.product_id,
            quantity=item.quantity, subtotal=subtotal,
            product=build_product_response(item.product)
        ))
    return schemas.CartResponse(items=cart_items, total=total, item_count=len(cart_items))


@router.get("/", response_model=schemas.CartResponse)
def get_cart(current_user: models.User = Depends(get_current_business), db: Session = Depends(get_db)):
    return build_cart_response(current_user.id, db)


@router.post("/", response_model=schemas.CartResponse)
def add_to_cart(
    data: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if data.quantity < product.min_order_qty:
        raise HTTPException(status_code=400, detail=f"Minimum order is {product.min_order_qty} {product.unit}")

    existing = db.query(models.CartItem).filter(
        models.CartItem.business_user_id == current_user.id,
        models.CartItem.product_id == data.product_id
    ).first()

    if existing:
        existing.quantity = data.quantity
    else:
        db.add(models.CartItem(business_user_id=current_user.id, product_id=data.product_id, quantity=data.quantity))

    db.commit()
    return build_cart_response(current_user.id, db)


@router.put("/{item_id}", response_model=schemas.CartResponse)
def update_cart_item(
    item_id: int, data: schemas.CartItemUpdate,
    current_user: models.User = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id, models.CartItem.business_user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    item.quantity = data.quantity
    db.commit()
    return build_cart_response(current_user.id, db)


@router.delete("/{item_id}", response_model=schemas.CartResponse)
def remove_from_cart(
    item_id: int,
    current_user: models.User = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id, models.CartItem.business_user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return build_cart_response(current_user.id, db)
