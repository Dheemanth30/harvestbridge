from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    role: str
    # Farmer fields
    farm_name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    certifications: Optional[str] = None
    produce_types: Optional[str] = None
    # Business fields
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    gst_number: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str


# ── Farmer ────────────────────────────────────────────────────────────────────
class FarmerProfileUpdate(BaseModel):
    farm_name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    certifications: Optional[str] = None
    produce_types: Optional[str] = None


class FarmerProfileResponse(BaseModel):
    id: int
    user_id: int
    farm_name: str
    location: Optional[str] = None
    description: Optional[str] = None
    certifications: Optional[str] = None
    produce_types: Optional[str] = None
    profile_image: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    class Config:
        from_attributes = True


# ── Product ───────────────────────────────────────────────────────────────────
class ProductResponse(BaseModel):
    id: int
    farmer_id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price_per_unit: float
    unit: str
    quantity_available: float
    min_order_qty: float
    is_organic: bool
    image_path: Optional[str] = None
    created_at: datetime
    farmer_name: Optional[str] = None
    farm_name: Optional[str] = None
    farmer_location: Optional[str] = None
    farmer_phone: Optional[str] = None

    class Config:
        from_attributes = True


# ── Cart ──────────────────────────────────────────────────────────────────────
class CartItemCreate(BaseModel):
    product_id: int
    quantity: float


class CartItemUpdate(BaseModel):
    quantity: float


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: float
    subtotal: float
    product: ProductResponse

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float
    item_count: int


# ── Orders ────────────────────────────────────────────────────────────────────
class OrderCreate(BaseModel):
    delivery_address: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: float
    unit_price: float
    product_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    business_user_id: int
    farmer_id: int
    total_amount: float
    status: str
    payment_status: str
    delivery_address: str
    created_at: datetime
    items: List[OrderItemResponse]
    farmer_name: Optional[str] = None
    farm_name: Optional[str] = None
    business_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str


# ── Payment ───────────────────────────────────────────────────────────────────
class PaymentSimulate(BaseModel):
    order_id: int
