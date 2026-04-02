from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..auth import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=schemas.TokenResponse)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if data.role not in ["farmer", "business"]:
        raise HTTPException(status_code=400, detail="Role must be 'farmer' or 'business'")
    if data.role == "farmer" and not data.farm_name:
        raise HTTPException(status_code=400, detail="Farm name required")
    if data.role == "business" and not data.business_name:
        raise HTTPException(status_code=400, detail="Business name required")

    user = models.User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.flush()

    if data.role == "farmer":
        db.add(models.FarmerProfile(
            user_id=user.id,
            farm_name=data.farm_name,
            location=data.location,
            description=data.description,
            certifications=data.certifications,
            produce_types=data.produce_types,
        ))
    else:
        db.add(models.BusinessProfile(
            user_id=user.id,
            business_name=data.business_name,
            business_type=data.business_type,
            location=data.location,
            gst_number=data.gst_number,
        ))

    db.commit()
    db.refresh(user)
    token = create_access_token({"user_id": user.id, "role": user.role})
    return schemas.TokenResponse(access_token=token, role=user.role, user_id=user.id, name=user.name)


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"user_id": user.id, "role": user.role})
    return schemas.TokenResponse(access_token=token, role=user.role, user_id=user.id, name=user.name)
