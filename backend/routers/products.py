import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, get_current_farmer
from ..config import UPLOAD_DIR

router = APIRouter()


def product_to_response(p: models.Product) -> schemas.ProductResponse:
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


async def save_image(image: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(await image.read())
    return f"/static/uploads/{filename}"


@router.get("/", response_model=List[schemas.ProductResponse])
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_organic: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    if search:
        q = q.filter(models.Product.name.ilike(f"%{search}%"))
    if is_organic is not None:
        q = q.filter(models.Product.is_organic == is_organic)
    return [product_to_response(p) for p in q.all()]


@router.get("/mine", response_model=List[schemas.ProductResponse])
def my_products(current_user: models.User = Depends(get_current_farmer), db: Session = Depends(get_db)):
    farmer = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == current_user.id).first()
    if not farmer:
        return []
    return [product_to_response(p) for p in farmer.products]


@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_response(p)


@router.post("/", response_model=schemas.ProductResponse)
async def create_product(
    name: str = Form(...), category: str = Form(...),
    description: Optional[str] = Form(None), price_per_unit: float = Form(...),
    unit: str = Form(...), quantity_available: float = Form(...),
    min_order_qty: float = Form(1.0), is_organic: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    farmer = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == current_user.id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    image_path = None
    if image and image.filename:
        image_path = await save_image(image)

    p = models.Product(
        farmer_id=farmer.id, name=name, category=category, description=description,
        price_per_unit=price_per_unit, unit=unit, quantity_available=quantity_available,
        min_order_qty=min_order_qty, is_organic=is_organic, image_path=image_path
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return product_to_response(p)


@router.put("/{product_id}", response_model=schemas.ProductResponse)
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None), category: Optional[str] = Form(None),
    description: Optional[str] = Form(None), price_per_unit: Optional[float] = Form(None),
    unit: Optional[str] = Form(None), quantity_available: Optional[float] = Form(None),
    min_order_qty: Optional[float] = Form(None), is_organic: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    farmer = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == current_user.id).first()
    if p.farmer_id != farmer.id:
        raise HTTPException(status_code=403, detail="Not your product")

    if name: p.name = name
    if category: p.category = category
    if description is not None: p.description = description
    if price_per_unit: p.price_per_unit = price_per_unit
    if unit: p.unit = unit
    if quantity_available is not None: p.quantity_available = quantity_available
    if min_order_qty: p.min_order_qty = min_order_qty
    if is_organic is not None: p.is_organic = is_organic
    if image and image.filename:
        p.image_path = await save_image(image)

    db.commit()
    db.refresh(p)
    return product_to_response(p)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: models.User = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    farmer = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == current_user.id).first()
    if p.farmer_id != farmer.id:
        raise HTTPException(status_code=403, detail="Not your product")
    db.delete(p)
    db.commit()
    return {"message": "Product deleted"}
