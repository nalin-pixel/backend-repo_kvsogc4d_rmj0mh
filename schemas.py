"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# Core domain schemas for the marketplace

class Supplier(BaseModel):
    name: str = Field(..., description="Factory or supplier name")
    summary: Optional[str] = Field(None, description="Short intro of the supplier/factory")
    location: Optional[str] = Field(None, description="City, Country")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating out of 5")
    logo_url: Optional[str] = Field(None, description="Logo or image URL")
    tags: List[str] = Field(default_factory=list, description="Capabilities or categories")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Unit price in USD")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
    supplier_id: str = Field(..., description="Reference to supplier")
    min_order_qty: int = Field(..., ge=1, description="Minimum order quantity required by factory")
    total_price: Optional[float] = Field(None, ge=0, description="Total price at MOQ")
    discount_rate: Optional[float] = Field(None, ge=0, le=1, description="Discount rate at MOQ (0-1)")
    customization_options: List[str] = Field(default_factory=list, description="Available customizations")

class SharedOrder(BaseModel):
    product_id: str = Field(..., description="Product being ordered together")
    supplier_id: str = Field(..., description="Supplier for the product")
    min_qty: int = Field(..., ge=1, description="MOQ required")
    pledged_qty: int = Field(0, ge=0, description="Total pledged quantity by participants")
    deadline: datetime = Field(..., description="Deadline to reach MOQ")
    participants: List[Dict] = Field(default_factory=list, description="List of {name,email,qty}")

class ContractRequest(BaseModel):
    company_name: str
    contact_email: str
    phone: Optional[str] = None
    details: str
    estimated_monthly_volume: Optional[int] = Field(None, ge=0)
    categories: List[str] = Field(default_factory=list)

# Example schemas kept for reference
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = Field(None, ge=0, le=120)
    is_active: bool = True
