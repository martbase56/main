# api/routers/admin.py (কাউন্টার ও রিলেশনাল জয়েনিং এরর ফিক্সড সম্পূর্ণ কোড)
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.database import supabase
from api.routers.auth import get_current_user

router = APIRouter()

class SettingsUpdateSchema(BaseModel):
    activation_fee: float
    dashboard_notice: str
    imgbb_api_key: str

# --- ১. হেল্পার ডিপেনডেন্সি: এডমিন রোল ভেরিফাই করা ---
def verify_admin(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.id
        admin_check = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        if not admin_check.data or admin_check.data['role'] != 'admin':
            raise HTTPException(status_code=403, detail="দুঃখিত, এই প্যানেলে প্রবেশাধিকার শুধুমাত্র এডমিনদের জন্য সীমাবদ্ধ।")
        return current_user
    except Exception:
        raise HTTPException(status_code=403, detail="এডমিন ভেরিফিকেশন ব্যর্থ হয়েছে।")


# --- ২. এন্ডপয়েন্ট: ড্যাশবোর্ড রিয়েল-টাইম স্ট্যাটস ---
@router.get("/stats")
def get_dashboard_stats(admin: dict = Depends(verify_admin)):
    try:
        # ক. মোট ইউজার সংখ্যা
        total_users_query = supabase.table("profiles").select("id").execute()
        total_users_count = len(total_users_query.data) if total_users_query.data else 0

        # খ. আজকের তারিখের শুরু (ISO Format in UTC)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_iso = today_start.isoformat()

        # গ. আজকের নতুন ইউজার সংখ্যা
        today_users_query = supabase.table("profiles").select("id").gte("created_at", today_start_iso).execute()
        today_users_count = len(today_users_query.data) if today_users_query.data else 0

        # ঘ. আজকের মোট অর্ডার ও টাকার পরিমাণ
        today_orders_query = supabase.table("orders").select("total_cost").gte("created_at", today_start_iso).execute()
        today_orders_count = len(today_orders_query.data) if today_orders_query.data else 0
        
        today_orders_data = today_orders_query.data
        today_amount = sum(float(order['total_cost']) for order in today_orders_data) if today_orders_data else 0.0

        return {
            "total_users": total_users_count,
            "today_users": today_users_count,
            "today_orders": today_orders_count,
            "today_amount": today_amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৩. এন্ডপয়েন্ট: পেন্ডিং অ্যাক্টিভেশন রিকোয়েস্ট তালিকা (ফরেন-কি জয়েনিং ফিক্সড) ---
@router.get("/activation-requests")
def get_pending_activation_requests(admin: dict = Depends(verify_admin)):
    try:
        # (গুরুত্বপূর্ণ ফিক্স) user_id ফরেন-কি স্পষ্ট করে দেওয়া হয়েছে [1.1.1, 1.2.5]
        query = supabase.table("activation_requests")\
            .select("*, profiles!user_id(full_name)")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৪. এন্ডপয়েন্ট: সকল অর্ডারের তালিকা (ফরেন-কি জয়েনিং ফিক্সড) ---
@router.get("/orders")
def get_all_orders(admin: dict = Depends(verify_admin)):
    try:
        # (গুরুত্বপূর্ণ ফিক্স) placed_by ফরেন-কি স্পষ্ট করে দেওয়া হয়েছে [1.1.1, 1.2.5]
        query = supabase.table("orders")\
            .select("*, profiles!placed_by(full_name)")\
            .order("created_at", desc=True)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৫. এন্ডপয়েন্ট: সিস্টেম সেটিংস রিড করা ---
@router.get("/get-settings")
def get_settings(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("system_settings").select("*").execute()
        settings_dict = {item['key']: item['value'] for item in query.data}
        return settings_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৬. এন্ডপয়েন্ট: সিস্টেম সেটিংস সেভ/আপডেট করা ---
@router.post("/update-settings")
def update_settings(data: SettingsUpdateSchema, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("system_settings").upsert({"key": "activation_fee", "value": str(data.activation_fee)}).execute()
        supabase.table("system_settings").upsert({"key": "dashboard_notice", "value": data.dashboard_notice}).execute()
        supabase.table("system_settings").upsert({"key": "imgbb_api_key", "value": data.imgbb_api_key}).execute()
        return {"status": "success", "message": "সিস্টেম সেটিংস সফলভাবে আপডেট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ব্যবহারকারী নিয়ন্ত্রণ এন্ডপয়েন্টসমূহ ====================

# --- ৭. এন্ডপয়েন্ট: সকল ব্যবহারকারীর তালিকা ফেচ করা ---
@router.get("/users")
def get_all_users(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৮. এন্ডপয়েন্ট: ব্যবহারকারীকে ব্যান করা ---
@router.post("/users/{user_id}/ban")
def ban_user(user_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("profiles").update({"is_active": False, "activation_status": "banned"}).eq("id", user_id).execute()
        return {"status": "success", "message": "ব্যবহারকারীকে সফলভাবে ব্যান করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৯. এন্ডপয়েন্ট: ব্যবহারকারীকে আনব্যান/একটিভ করা ---
@router.post("/users/{user_id}/unban")
def unban_user(user_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("profiles").update({"is_active": True, "activation_status": "active"}).eq("id", user_id).execute()
        return {"status": "success", "message": "ব্যবহারকারীকে সফলভাবে সচল ও অ্যাক্টিভ করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ১০. এন্ডপয়েন্ট: ইউজার অ্যাকাউন্ট এবং প্রোফাইল ডিলিট করা ---
@router.delete("/users/{user_id}")
def delete_user_account(user_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.auth.admin.delete_user(user_id)
        supabase.table("profiles").delete().eq("id", user_id).execute()
        return {"status": "success", "message": "ব্যবহারকারীর অ্যাকাউন্ট ও প্রোফাইল ডাটাবেজ থেকে চিরতরে ডিলিট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
