import os
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import List, Optional
from api.database import supabase
from api.routers.auth import get_current_user

router = APIRouter()

class ProductCreateSchema(BaseModel):
    name: str
    description: str = None
    sizes: str = None
    colors: str = None
    price: float                        
    customer_offer_price: float = None
    reseller_price: float
    reseller_hold_bonus: float = 0.0
    images: list[str] = []              
    stock: int = 0
    category_id: str = None
    subcategory: str = None
    warranty_type: str = "no"           
    warranty_days: int = 0
    product_code: str
    is_offer: bool = False
    reseller_offer_price: float = None

class ProductUpdateSchema(BaseModel):
    name: str
    description: str = None
    sizes: str = None
    colors: str = None
    price: float
    customer_offer_price: float = None
    reseller_price: float
    reseller_hold_bonus: float = 0.0
    images: List[str] = []
    stock: int = 0
    category_id: str = None
    subcategory: str = None
    warranty_type: str = "no"
    warranty_days: int = 0
    product_code: str
    is_offer: bool = False
    reseller_offer_price: float = None

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    settings_query = supabase.table("system_settings").select("value").eq("key", "imgbb_api_key").single().execute()
    if not settings_query.data:
        raise HTTPException(status_code=400, detail="সিস্টেম সেটিংসে ImgBB API Key সেটআপ করা হয়নি।")
    
    api_key = settings_query.data['value']
    contents = await file.read()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.imgbb.com/1/upload",
                params={"key": api_key},
                files={"image": (file.filename, contents)}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="ImgBB-তে ছবি আপলোড করতে ব্যর্থ হয়েছে।")
            
            res_data = response.json()
            return {"url": res_data['data']['url']}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"সার্ভার ত্রুটি: {str(e)}")

@router.post("/add")
def add_product(data: ProductCreateSchema, admin_user: dict = Depends(get_current_user)):
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাডমিনরাই নতুন পণ্য যোগ করতে পারবেন।")

    product_payload = {
        "title": data.name,
        "description": data.description,
        "sizes": data.sizes,
        "colors": data.colors,
        "regular_price": data.price,
        "customer_offer_price": data.customer_offer_price if data.is_offer else None,
        "reseller_price": data.reseller_price,
        "reseller_hold_bonus": data.reseller_hold_bonus,
        "images": data.images,
        "stock": data.stock,
        "category_id": data.category_id if data.category_id else None,
        "subcategory": data.subcategory,
        "warranty_type": data.warranty_type,
        "warranty_days": data.warranty_days if data.warranty_type == "yes" else 0,
        "product_code": data.product_code,
        "is_offer": data.is_offer,
        "reseller_offer_price": data.reseller_offer_price if data.is_offer else None
    }

    try:
        query = supabase.table("products").insert(product_payload).execute()
        return {"status": "success", "message": "পণ্যটি সফলভাবে যোগ করা হয়েছে।", "product": query.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"পণ্য যোগ করতে ব্যর্থ: {str(e)}")

@router.put("/update/{product_id}")
def update_product(product_id: str, data: ProductUpdateSchema, admin_user: dict = Depends(get_current_user)):
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="অনুমতি নেই।")

    product_payload = {
        "title": data.name,
        "description": data.description,
        "sizes": data.sizes,
        "colors": data.colors,
        "regular_price": data.price,
        "customer_offer_price": data.customer_offer_price if data.is_offer else None,
        "reseller_price": data.reseller_price,
        "reseller_hold_bonus": data.reseller_hold_bonus,
        "images": data.images,
        "stock": data.stock,
        "category_id": data.category_id if data.category_id else None,
        "subcategory": data.subcategory,
        "warranty_type": data.warranty_type,
        "warranty_days": data.warranty_days if data.warranty_type == "yes" else 0,
        "product_code": data.product_code,
        "is_offer": data.is_offer,
        "reseller_offer_price": data.reseller_offer_price if data.is_offer else None
    }

    try:
        query = supabase.table("products").update(product_payload).eq("id", product_id).execute()
        return {"status": "success", "message": "পণ্যটির বিবরণ সফলভাবে আপডেট করা হয়েছে।", "product": query.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"আপডেট ব্যর্থ: {str(e)}")

@router.delete("/delete/{product_id}")
def delete_product(product_id: str, admin_user: dict = Depends(get_current_user)):
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="অনুমতি নেই।")
    
    try:
        supabase.table("products").delete().eq("id", product_id).execute()
        return {"status": "success", "message": "পণ্যটি ডাটাবেজ থেকে চিরতরে ডিলিট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ডিলিট ব্যর্থ: {str(e)}")
