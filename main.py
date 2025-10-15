# main.py
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# --------- XAMPP / MySQL config ---------
# Default XAMPP: user 'root' with empty password. Create DB 'products_db' in phpMyAdmin.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:@127.0.0.1:3306/products_db?charset=utf8mb4",  # change if you set a password
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# --------- SQLAlchemy table ---------
class ProductORM(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(1000), nullable=True)

Base.metadata.create_all(bind=engine)  # create table if not exists

# --------- Pydantic schemas ---------
class Product(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None

    class Config:
        from_attributes = True  # allow ORM -> schema

class ProductCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

# --------- FastAPI app ---------
app = FastAPI(title="Product Catalog API", description="Simple product catalog")

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET /products
@app.get("/products", response_model=List[Product])
def list_products(db: Session = Depends(get_db)):
    items = db.query(ProductORM).order_by(ProductORM.id.asc()).all()
    return [Product.model_validate(i) for i in items]

# GET /products/{product_id}
@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    item = db.get(ProductORM, product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product.model_validate(item)

# POST /products  (not exposed to MCP)
@app.post("/products", response_model=Product, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    item = ProductORM(name=payload.name, price=payload.price, description=payload.description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return Product.model_validate(item)
