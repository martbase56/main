# api/routers/products.py
import os
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends
from pydantic import BaseModel
from api.database import supabase
from api.routers.auth import get_current_user # পূর্বের মেথড থেকে এডমিন চেক করার জন্য

router = APIRouter()

# --- ১. Pydantic ডেটা ভ্যালিডেশন স্কিমা ---
class ProductCreateSchema(BaseModel):
    name: str
    description: str = None
    sizes: str = None
    colors: str = None
    price: float                        -- regular_price
    customer_offer_price: float = None
    reseller_price: float
    reseller_hold_bonus: float = 0.0
    images: list[str] = []              -- সর্বোচ্চ ৪টি ছবির লিংক
    stock: int = 0
    category_id: str = None
    subcategory: str = None
    warranty_type: str = "no"           -- 'yes' অথবা 'no'
    warranty_days: int = 0
    product_code: str


# --- ২. সিকিউর ইমেজ আপলোড এন্ডপয়েন্ট (ImgBB Gateway) ---
@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    # ক. ডাটাবেজ থেকে সিকিউর উপায়ে ImgBB API Key রিড করা
    settings_query = supabase.table("system_settings").select("value").eq("key", "imgbb_api_key").single().execute()
    if not settings_query.data:
        raise HTTPException(status_code=400, detail="সিস্টেম সেটিংসে ImgBB API Key সেটআপ করা হয়নি।")
    
    api_key = settings_query.data['value']
    
    # খ. আপলোড করা ফাইল কনটেন্ট রিড করা
    contents = await file.read()
    
    # গ. httpx এর মাধ্যমে ব্যাকএন্ড থেকে নিরাপদে ImgBB-তে ছবি পোস্ট করা
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


# --- ৩. সিকিউর এন্ডপয়েন্ট: নতুন প্রোডাক্ট যোগ করা (শুধুমাত্র এডমিনদের জন্য) ---
@router.post("/add")
def add_product(data: ProductCreateSchema, admin_user: dict = Depends(get_current_user)):
    # এডমিন কিনা যাচাই করা
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাডমিনরাই নতুন পণ্য যোগ করতে পারবেন।")

    # ডাটাবেজ ইনসার্ট পে-লোড প্রস্তুত করা
    product_payload = {
        "title": data.name, # ডাটাবেজ কলাম 'title' এ প্রোডাক্ট নেম সেভ হবে
        "description": data.description,
        "sizes": data.sizes,
        "colors": data.colors,
        "regular_price": data.price,
        "customer_offer_price": data.customer_offer_price,
        "reseller_price": data.reseller_price,
        "reseller_hold_bonus": data.reseller_hold_bonus,
        "images": data.images,
        "stock": data.stock,
        "category_id": data.category_id if data.category_id else None,
        "subcategory": data.subcategory,
        "warranty_type": data.warranty_type,
        "warranty_days": data.warranty_days if data.warranty_type == "yes" else 0,
        "product_code": data.product_code
    }

    try:
        query = supabase.table("products").insert(product_payload).execute()
        return {"status": "success", "message": "পণ্যটি সফলভাবে যোগ করা হয়েছে।", "product": query.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"পণ্য যোগ করতে ব্যর্থ: {str(e)}")
