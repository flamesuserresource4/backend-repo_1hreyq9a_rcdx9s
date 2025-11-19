import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Brand, DeviceModel, RepairPartPrice, Location, Review, Inquiry

app = FastAPI(title="Handy Reparatur 2GO API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"name": "Handy Reparatur 2GO", "owner": "Tech Repair Partners GmbH", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Seed data helper (idempotent)
@app.post("/seed")
def seed_basic_data():
    brands = [
        {"name": "Apple", "slug": "apple", "logo_url": ""},
        {"name": "Samsung", "slug": "samsung", "logo_url": ""},
        {"name": "Xiaomi", "slug": "xiaomi", "logo_url": ""},
        {"name": "Google", "slug": "google", "logo_url": ""},
    ]
    for b in brands:
        existing = list(db["brand"].find({"slug": b["slug"]}).limit(1)) if db else []
        if not existing and db:
            create_document("brand", Brand(**b))

    # Minimal models
    models = [
        {"brand": "apple", "name": "iPhone 13", "code": "iphone-13", "category": "phone"},
        {"brand": "apple", "name": "iPad Air (4th Gen)", "code": "ipad-air-4", "category": "tablet"},
        {"brand": "samsung", "name": "Galaxy S21", "code": "galaxy-s21", "category": "phone"},
        {"brand": "xiaomi", "name": "Redmi Note 10", "code": "redmi-note-10", "category": "phone"},
        {"brand": "google", "name": "Pixel 7", "code": "pixel-7", "category": "phone"},
    ]
    for m in models:
        existing = list(db["devicemodel"].find({"code": m["code"]}).limit(1)) if db else []
        if not existing and db:
            create_document("devicemodel", DeviceModel(**m))

    # Sample part prices
    prices = [
        {"brand": "apple", "model": "iphone-13", "part": "Display", "price_eur": 199.0, "duration_min": 60, "warranty_months": 12},
        {"brand": "apple", "model": "iphone-13", "part": "Akku", "price_eur": 79.0, "duration_min": 30, "warranty_months": 12},
        {"brand": "samsung", "model": "galaxy-s21", "part": "Display", "price_eur": 189.0, "duration_min": 60, "warranty_months": 12},
        {"brand": "xiaomi", "model": "redmi-note-10", "part": "Display", "price_eur": 129.0, "duration_min": 60, "warranty_months": 12},
        {"brand": "google", "model": "pixel-7", "part": "Akku", "price_eur": 89.0, "duration_min": 45, "warranty_months": 12},
    ]
    for p in prices:
        existing = list(db["repairpartprice"].find({"model": p["model"], "part": p["part"]}).limit(1)) if db else []
        if not existing and db:
            create_document("repairpartprice", RepairPartPrice(**p))

    # Example location
    locations = [
        {"name": "Berlin Mitte", "address": "Friedrichstr. 123", "city": "Berlin", "postal_code": "10117", "phone": "+49 30 123456"},
        {"name": "München Zentrum", "address": "Marienplatz 1", "city": "München", "postal_code": "80331", "phone": "+49 89 123456"},
    ]
    for loc in locations:
        existing = list(db["location"].find({"name": loc["name"]}).limit(1)) if db else []
        if not existing and db:
            create_document("location", Location(**loc))

    return {"status": "ok"}

# Public endpoints
class PriceQuery(BaseModel):
    brand: str
    model: str

@app.get("/brands", response_model=List[Brand])
def list_brands():
    docs = get_documents("brand") if db else []
    return [Brand(**{k: v for k, v in d.items() if k != "_id"}) for d in docs]

@app.get("/models", response_model=List[DeviceModel])
def list_models(brand: Optional[str] = None):
    filt = {"brand": brand} if brand else {}
    docs = get_documents("devicemodel", filt) if db else []
    return [DeviceModel(**{k: v for k, v in d.items() if k != "_id"}) for d in docs]

@app.get("/parts", response_model=List[str])
def list_parts(brand: Optional[str] = None, model: Optional[str] = None):
    filt = {}
    if brand: filt["brand"] = brand
    if model: filt["model"] = model
    docs = get_documents("repairpartprice", filt) if db else []
    parts = sorted({d.get("part") for d in docs})
    return [p for p in parts if p]

@app.get("/price")
def get_price(brand: str, model: str, part: str):
    doc = db["repairpartprice"].find_one({"brand": brand, "model": model, "part": part}) if db else None
    if not doc:
        raise HTTPException(status_code=404, detail="Price not found")
    doc.pop("_id", None)
    return doc

@app.get("/locations", response_model=List[Location])
def get_locations():
    docs = get_documents("location") if db else []
    return [Location(**{k: v for k, v in d.items() if k != "_id"}) for d in docs]

@app.get("/reviews", response_model=List[Review])
def get_reviews(limit: int = 6):
    docs = get_documents("review", limit=limit) if db else []
    if not docs:
        # Fallback sample reviews
        docs = [
            {"author": "Max Müller", "rating": 5, "text": "Schnell und fairer Preis!", "source": "Google"},
            {"author": "Anna Schmidt", "rating": 5, "text": "Sehr freundlich, mein iPhone ist wie neu.", "source": "Google"},
            {"author": "Jonas Weber", "rating": 4, "text": "Gute Beratung, gerne wieder.", "source": "Google"},
        ]
    return [Review(**{k: v for k, v in d.items() if k != "_id"}) for d in docs]

@app.post("/inquiry")
def submit_inquiry(data: Inquiry):
    if db:
        create_document("inquiry", data)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
