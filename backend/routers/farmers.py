from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_farmer

router = APIRouter()


@router.get("/", response_model=List[schemas.FarmerProfileResponse])
def list_farmers(db: Session = Depends(get_db)):
    farmers = db.query(models.FarmerProfile).all()
    return [
        schemas.FarmerProfileResponse(
            id=f.id, user_id=f.user_id, farm_name=f.farm_name,
            location=f.location, description=f.description,
            certifications=f.certifications, produce_types=f.produce_types,
            profile_image=f.profile_image,
            user_name=f.user.name if f.user else None,
            user_email=f.user.email if f.user else None,
            user_phone=f.user.phone if f.user else None,
        ) for f in farmers
    ]


@router.get("/me", response_model=schemas.FarmerProfileResponse)
def get_my_profile(current_user: models.User = Depends(get_current_farmer), db: Session = Depends(get_db)):
    farmer = db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == current_user.id).first()
    return schemas.FarmerProfileResponse(
        id=farmer.id, user_id=farmer.user_id, farm_name=farmer.farm_name,
        location=farmer.location, description=farmer.description,
        certifications=farmer.certifications, produce_types=farmer.produce_types,
        profile_image=farmer.profile_image,
        user_name=current_user.name, user_email=current_user.email, user_phone=current_user.phone,
    )
