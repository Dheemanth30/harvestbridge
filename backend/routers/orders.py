from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from collections import defaultdict
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, get_current_business, get_current_farmer

router = APIRouter()

VALID_STATUSES = ["pending", "confirmed", "packed", "shipped", "delivered"]


def build_order_response(order: models.Order) -> schemas.OrderResponse:
    items = [
        schemas.OrderItemResponse(
            id=i.id, product_id=i.product_id, quantity=i.quantity,
            unit_price=i.unit_price,
            product_name=i.product.name if i.product else None
        ) for i in order.items
    ]
    return schemas.OrderResponse(
        id=order.id, business_user_id=order.business_user_id,
        farmer_id=order.farmer_id, total_amount=order.total_amount,
        status=order.status, payment_status=order.payment_status,
        delivery_address=order.delivery_address, created_at=order.created_at,
        items=items,
        farmer_name=order.farmer.user.name if order.farmer and order.farmer.user else None,
        farm_name=order.farmer.farm_name if order.farmer else None,
        business_name=order.business_user.business_profile.business_name
        if order.business_user and order.business_user.business_profile else None,
    )


@router.post("/", response_model=List[schemas.OrderResponse])
def place_order(
    data: schemas.OrderCreate,
    current_user: models.User = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    cart_items = db.query(models.CartItem).filter(
        models.CartItem.business_user_id == current_user.id
    ).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Group by farmer
    farmer_items = defaultdict(list)
    for item in cart_items:
        farmer_items[item.product.farmer_id].append(item)

    orders = []
    for farmer_id, items in farmer_items.items():
        total = sum(i.quantity * i.product.price_per_unit for i in items)
        order = models.Order(
            business_user_id=current_user.id, farmer_id=farmer_id,
            total_amount=total, delivery_address=data.delivery_address,
            status="pending", payment_status="unpaid"
        )
        db.add(order)
        db.flush()
        for item in items:
            db.add(models.OrderItem(
                order_id=order.id, product_id=item.product_id,
                quantity=item.quantity, unit_price=item.product.price_per_unit
            ))
        orders.append(order)

    for item in cart_items:
        db.delete(item)

    db.commit()
    for o in orders:
        db.refresh(o)

    return [build_order_response(o) for o in orders]


@router.get("/mine", response_model=List[schemas.OrderResponse])
def get_my_orders(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "business":
        orders = db.query(models.Order).filter(
            models.Order.business_user_id == current_user.id
        ).order_by(models.Order.created_at.desc()).all()
    else:
        farmer = db.query(models.FarmerProfile).filter(
            models.FarmerProfile.user_id == current_user.id
        ).first()
        orders = db.query(models.Order).filter(
            models.Order.farmer_id == farmer.id
        ).order_by(models.Order.created_at.desc()).all() if farmer else []

    return [build_order_response(o) for o in orders]


@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role == "business" and order.business_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "farmer":
        farmer = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == current_user.id).first()
        if not farmer or order.farmer_id != farmer.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return build_order_response(order)


@router.put("/{order_id}/status")
def update_order_status(
    order_id: int, data: schemas.OrderStatusUpdate,
    current_user: models.User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {VALID_STATUSES}")
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    farmer = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == current_user.id).first()
    if not farmer or order.farmer_id != farmer.id:
        raise HTTPException(status_code=403, detail="Not your order")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return build_order_response(order)
