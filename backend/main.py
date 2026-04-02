import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine
from . import models
from .routers import auth_router, products, cart, orders, payments, farmers

# Create all tables
models.Base.metadata.create_all(bind=engine)

# Create upload directory
os.makedirs("static/uploads", exist_ok=True)

app = FastAPI(title="HarvestBridge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes (must be registered BEFORE static files mount)
app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(farmers.router, prefix="/api/farmers", tags=["Farmers"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])

# Static file mounts
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
