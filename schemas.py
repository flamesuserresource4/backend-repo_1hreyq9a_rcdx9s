"""
Database Schemas for Handy Reparatur 2GO

Each Pydantic model maps to a MongoDB collection (lowercased class name).
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Brand(BaseModel):
    name: str = Field(..., description="Brand name e.g. Apple, Samsung, Xiaomi, Google")
    slug: str = Field(..., description="URL-friendly identifier")
    logo_url: Optional[str] = Field(None, description="Public logo URL")

class DeviceModel(BaseModel):
    brand: str = Field(..., description="Brand slug this model belongs to")
    name: str = Field(..., description="Model display name e.g. iPhone 13 Pro")
    code: str = Field(..., description="Model code/slug e.g. iphone-13-pro")
    category: str = Field(..., description="phone | tablet | smartwatch | other")

class RepairPartPrice(BaseModel):
    brand: str = Field(..., description="Brand slug")
    model: str = Field(..., description="Model code/slug")
    part: str = Field(..., description="Repair part name e.g. Display, Akku, Kamera")
    price_eur: float = Field(..., ge=0, description="Price in EUR")
    duration_min: int = Field(60, ge=5, le=480, description="Approx. duration in minutes")
    warranty_months: int = Field(6, ge=0, le=36, description="Warranty period in months")

class Location(BaseModel):
    name: str
    address: str
    city: str
    postal_code: str
    phone: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    hours: Optional[str] = Field(None, description="Opening hours text")

class Review(BaseModel):
    author: str
    rating: int = Field(..., ge=1, le=5)
    text: str
    source: str = Field("Google", description="Review source platform")
    profile_url: Optional[str] = None

class Inquiry(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str
    brand: Optional[str] = None
    model: Optional[str] = None
    part: Optional[str] = None
