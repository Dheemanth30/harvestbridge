from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_business

router = APIRouter()


@router.post("/simulate")
def simulate_payment(
    data: schemas.PaymentSimulate,
    current_user: models.User = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    """Simulate payment — marks the order as paid instantly."""
    order = db.query(models.Order).filter(models.Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.business_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    if order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Order already paid")

    order.payment_status = "paid"
    order.status = "confirmed"
    db.commit()
    return {"message": "Payment simulated successfully", "order_id": order.id, "payment_status": "paid"}
