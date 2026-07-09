# api/routers/telegram.py
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.database import supabase
from api.routers.admin import verify_admin

router = APIRouter()

# --- Pydantic স্কিমাস ---
class TGOrderCreateSchema(BaseModel):
    user_id: str
    telegram_username: str
    service_type: str                  # 'premium' or 'stars'
    package_title: str
    price: float
    payment_method: str                # 'bKash' or 'Nagad'
    payment_details: Dict[str, Any]    # {"sender_number": "...", "trx_id": "..."}

class TGPackageUpdateSchema(BaseModel):
    service_type: str
    title: str
    price: float
    duration_or_qty: int

# --- ১. এন্ডপয়েন্ট: সকল টেলিগ্রাম প্যাকেজ লোড করা (পাবলিক) ---
@router.get("/packages")
def get_telegram_packages():
    try:
        query = supabase.table("telegram_packages").select("*").order("price", desc=False).execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ২. এন্ডপয়েন্ট: ব্যবহারকারী কর্তৃক টেলিগ্রাম অর্ডার প্লেস করা ---
@router.post("/order")
def place_telegram_order(order: TGOrderCreateSchema):
    try:
        payload = {
            "user_id": order.user_id,
            "telegram_username": order.telegram_username.strip().replace("@", ""),
            "service_type": order.service_type,
            "package_title": order.package_title,
            "price": order.price,
            "payment_method": order.payment_method,
            "payment_details": order.payment_details,
            "status": "pending"
        }
        query = supabase.table("telegram_orders").insert(payload).execute()
        return {"status": "success", "message": "আপনার টেলিগ্রাম অর্ডারটি সফলভাবে জমা হয়েছে।", "order": query.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ৩. এন্ডপয়েন্ট: ব্যবহারকারীর নিজস্ব অর্ডারের হিস্ট্রি লোড ---
@router.get("/history/{user_id}")
def get_user_tg_history(user_id: str):
    try:
        query = supabase.table("telegram_orders").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== এডমিন এন্ডপয়েন্টসমূহ ====================

# --- ৪. এন্ডপয়েন্ট: এডমিন প্যানেলের জন্য সকল টেলিগ্রাম অর্ডার লোড ---
@router.get("/admin/orders")
def get_all_tg_orders(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("telegram_orders")\
            .select("*, profiles!user_id(full_name, phone_number)")\
            .order("created_at", desc=True)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ৫. এন্ডপয়েন্ট: এডমিন কর্তৃক প্যাকেজ তৈরি বা সংশোধন ---
@router.post("/admin/upsert-package")
def upsert_tg_package(data: TGPackageUpdateSchema, admin: dict = Depends(verify_admin)):
    try:
        payload = {
            "service_type": data.service_type,
            "title": data.title,
            "price": data.price,
            "duration_or_qty": data.duration_or_qty
        }
        # নতুন প্যাক তৈরি বা এক্সিস্টিং আপডেট
        query = supabase.table("telegram_packages").upsert(payload, on_conflict="title").execute()
        return {"status": "success", "message": "প্যাকেজের তথ্য সফলভাবে সেভ করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ৬. এন্ডপয়েন্ট: কাস্টম প্যাকেজ ডিলিট করা ---
@router.delete("/admin/delete-package/{package_id}")
def delete_tg_package(package_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("telegram_packages").delete().eq("id", package_id).execute()
        return {"status": "success", "message": "প্যাকেজটি সফলভাবে ডিলিট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ৭. এন্ডপয়েন্ট: টেলিগ্রাম অর্ডার অনুমোদন করা ---
@router.post("/admin/approve-order/{order_id}")
def approve_tg_order(order_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("telegram_orders").update({"status": "approved"}).eq("id", order_id).execute()
        return {"status": "success", "message": "টেলিগ্রাম অর্ডারটি সফলভাবে অ্যাপ্রুভ করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ৮. এন্ডপয়েন্ট: টেলিগ্রাম অর্ডার বাতিল করা ---
@router.post("/admin/reject-order/{order_id}")
def reject_tg_order(order_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("telegram_orders").update({"status": "rejected"}).eq("id", order_id).execute()
        return {"status": "success", "message": "টেলিগ্রাম অর্ডারটি বাতিল/রিজেক্ট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
