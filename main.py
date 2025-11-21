import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Supplier, Product, SharedOrder, ContractRequest

app = FastAPI(title="SupplyLink API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "SupplyLink backend running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# --------- Seed demo data if collections are empty ----------

def ensure_demo_data():
    try:
        if db is None:
            return
        # Seed suppliers
        if db["supplier"].count_documents({}) == 0:
            suppliers = [
                {
                    "name": "NovaFab Industries",
                    "summary": "Precision electronics assembly with global certifications.",
                    "location": "Shenzhen, China",
                    "rating": 4.7,
                    "logo_url": "https://images.unsplash.com/photo-1581090464777-f3220bbe1b8b",
                    "tags": ["electronics", "assembly", "ISO9001"]
                },
                {
                    "name": "GreenThread Textiles",
                    "summary": "Sustainable garment manufacturing at scale.",
                    "location": "Dhaka, Bangladesh",
                    "rating": 4.5,
                    "logo_url": "https://images.unsplash.com/photo-1520975940200-695d9a720b4a",
                    "tags": ["apparel", "organic", "ethical"]
                },
                {
                    "name": "Form & Flow Plastics",
                    "summary": "Injection molded parts with rapid tooling.",
                    "location": "Guadalajara, Mexico",
                    "rating": 4.6,
                    "logo_url": "https://images.unsplash.com/photo-1581090464777-f3220bbe1b8b",
                    "tags": ["plastics", "molding", "prototyping"]
                },
            ]
            for s in suppliers:
                create_document("supplier", s)
        # Seed products
        if db["product"].count_documents({}) == 0:
            supplier_ids = [str(doc["_id"]) for doc in db["supplier"].find({}).limit(3)]
            products = [
                {
                    "title": "Smart LED Panel",
                    "description": "Modular LED panel for retail displays.",
                    "price": 49.0,
                    "category": "Electronics",
                    "in_stock": True,
                    "supplier_id": supplier_ids[0],
                    "min_order_qty": 200,
                    "total_price": 9800,
                    "discount_rate": 0.12,
                    "customization_options": ["Size", "Color Temperature", "Branding"]
                },
                {
                    "title": "Organic Cotton T-Shirt",
                    "description": "Soft, durable, eco-friendly shirts.",
                    "price": 6.5,
                    "category": "Apparel",
                    "in_stock": True,
                    "supplier_id": supplier_ids[1],
                    "min_order_qty": 500,
                    "total_price": 3250,
                    "discount_rate": 0.08,
                    "customization_options": ["Color", "Print", "Labeling"]
                },
                {
                    "title": "Injection Molded Enclosure",
                    "description": "ABS enclosure for electronics projects.",
                    "price": 2.1,
                    "category": "Plastics",
                    "in_stock": True,
                    "supplier_id": supplier_ids[2],
                    "min_order_qty": 1000,
                    "total_price": 2100,
                    "discount_rate": 0.1,
                    "customization_options": ["Material", "Finish", "Color"]
                },
            ]
            for p in products:
                create_document("product", p)
        # Seed shared orders
        if db["sharedorder"].count_documents({}) == 0:
            prod_docs = list(db["product"].find({}).limit(3))
            now = datetime.utcnow()
            shared_orders = [
                {
                    "product_id": str(prod_docs[0]["_id"]),
                    "supplier_id": prod_docs[0]["supplier_id"],
                    "min_qty": prod_docs[0]["min_order_qty"],
                    "pledged_qty": 140,
                    "deadline": now + timedelta(days=6, hours=5),
                    "participants": [
                        {"name": "Atlas Retail", "email": "atlas@example.com", "qty": 100},
                        {"name": "Local Boutique", "email": "boutique@example.com", "qty": 40}
                    ]
                },
                {
                    "product_id": str(prod_docs[1]["_id"]),
                    "supplier_id": prod_docs[1]["supplier_id"],
                    "min_qty": prod_docs[1]["min_order_qty"],
                    "pledged_qty": 460,
                    "deadline": now + timedelta(days=2, hours=12),
                    "participants": [
                        {"name": "Gym Chain", "email": "gym@example.com", "qty": 300},
                        {"name": "Boutique", "email": "fashion@example.com", "qty": 160}
                    ]
                }
            ]
            for so in shared_orders:
                create_document("sharedorder", so)
    except Exception:
        # Silent fail in case DB not configured
        pass

ensure_demo_data()

# -------------------- Models for requests --------------------

class SearchQuery(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    supplier: Optional[str] = None

# ---------------------- API Endpoints ------------------------

@app.get("/api/suppliers")
def list_suppliers(q: Optional[str] = Query(None), tag: Optional[str] = Query(None)):
    filter_dict = {}
    if q:
        filter_dict["name"] = {"$regex": q, "$options": "i"}
    if tag:
        filter_dict["tags"] = tag
    items = get_documents("supplier", filter_dict)
    for it in items:
        it["id"] = str(it.pop("_id", ""))
    return {"items": items}

@app.get("/api/products")
def list_products(q: Optional[str] = Query(None), category: Optional[str] = Query(None), supplier: Optional[str] = Query(None)):
    filter_dict = {}
    if q:
        filter_dict["title"] = {"$regex": q, "$options": "i"}
    if category:
        filter_dict["category"] = category
    if supplier:
        filter_dict["supplier_id"] = supplier
    items = get_documents("product", filter_dict)
    for it in items:
        it["id"] = str(it.pop("_id", ""))
    return {"items": items}

@app.get("/api/supplier/{supplier_id}/products")
def products_by_supplier(supplier_id: str):
    items = get_documents("product", {"supplier_id": supplier_id})
    for it in items:
        it["id"] = str(it.pop("_id", ""))
    return {"items": items}

@app.get("/api/shared-orders")
def list_shared_orders():
    items = get_documents("sharedorder")
    for it in items:
        it["id"] = str(it.pop("_id", ""))
    return {"items": items}

@app.post("/api/shared-orders/{order_id}/pledge")
def pledge_to_shared_order(order_id: str, qty: int = Query(..., ge=1), name: str = Query("Guest"), email: Optional[str] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = db["sharedorder"].find_one({"_id": db["sharedorder"].database.client.get_default_database().codec_options.document_class.objectid_class(order_id)})
    # Fallback simple lookup by _id string conversion
    if not doc:
        try:
            from bson import ObjectId
            doc = db["sharedorder"].find_one({"_id": ObjectId(order_id)})
        except Exception:
            doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Shared order not found")
    db["sharedorder"].update_one({"_id": doc["_id"]}, {"$inc": {"pledged_qty": qty}, "$push": {"participants": {"name": name, "email": email, "qty": qty}}})
    updated = db["sharedorder"].find_one({"_id": doc["_id"]})
    updated["id"] = str(updated.pop("_id", ""))
    return updated

@app.post("/api/contracts")
def create_contract_request(payload: ContractRequest):
    new_id = create_document("contractrequest", payload)
    return {"id": new_id, "status": "received"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
