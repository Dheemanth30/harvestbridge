from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'farmer' or 'business'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    business_profile = relationship("BusinessProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders_placed = relationship("Order", back_populates="business_user", foreign_keys="Order.business_user_id")


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    farm_name = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    certifications = Column(String(500))
    produce_types = Column(String(500))
    profile_image = Column(String(500))

    user = relationship("User", back_populates="farmer_profile")
    products = relationship("Product", back_populates="farmer", cascade="all, delete-orphan")
    orders_received = relationship("Order", back_populates="farmer", foreign_keys="Order.farmer_id")


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100))
    location = Column(String(255))
    gst_number = Column(String(50))

    user = relationship("User", back_populates="business_profile")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    price_per_unit = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    quantity_available = Column(Float, default=0)
    min_order_qty = Column(Float, default=1.0)
    is_organic = Column(Boolean, default=False)
    image_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer = relationship("FarmerProfile", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    business_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    business_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")
    payment_status = Column(String(50), default="unpaid")
    delivery_address = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    business_user = relationship("User", back_populates="orders_placed", foreign_keys=[business_user_id])
    farmer = relationship("FarmerProfile", back_populates="orders_received", foreign_keys=[farmer_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
