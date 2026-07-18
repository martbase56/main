
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
    
def verify_admin(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.id
        admin_check = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        if not admin_check.data or admin_check.data['role'] != 'admin':
            raise HTTPException(status_code=403, detail="দুঃখিত, এই প্যানেলে প্রবেশাধিকার শুধুমাত্র এডমিনদের জন্য সীমাবদ্ধ।")
        return current_user
    except Exception:
        raise HTTPException(status_code=403, detail="এডমিন ভেরিফিকেশন ব্যর্থ হয়েছে।")

@router.get("/stats")
def get_dashboard_stats(admin: dict = Depends(verify_admin)):
    try:
        
        total_users_query = supabase.table("profiles").select("id").execute()
        total_users_count = len(total_users_query.data) if total_users_query.data else 0
        
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_iso = today_start.isoformat()

        
        today_users_query = supabase.table("profiles").select("id").gte("created_at", today_start_iso).execute()
        today_users_count = len(today_users_query.data) if today_users_query.data else 0
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

@router.get("/activation-requests")
def get_pending_activation_requests(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("activation_requests")\
            .select("*, profiles!user_id(full_name)")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/orders")
def get_all_orders(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("orders")\
            .select("*, profiles!placed_by(full_name)")\
            .order("created_at", desc=True)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-settings")
def get_settings(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("system_settings").select("*").execute()
        settings_dict = {item['key']: item['value'] for item in query.data}
        return settings_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-settings")
def update_settings(data: SettingsUpdateSchema, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("system_settings").upsert({"key": "activation_fee", "value": str(data.activation_fee)}).execute()
        supabase.table("system_settings").upsert({"key": "dashboard_notice", "value": data.dashboard_notice}).execute()
        supabase.table("system_settings").upsert({"key": "imgbb_api_key", "value": data.imgbb_api_key}).execute()
        return {"status": "success", "message": "সিস্টেম সেটিংস সফলভাবে আপডেট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
def get_all_users(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/ban")
def ban_user(user_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("profiles").update({"is_active": False, "activation_status": "banned"}).eq("id", user_id).execute()
        return {"status": "success", "message": "ব্যবহারকারীকে সফলভাবে ব্যান করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/unban")
def unban_user(user_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("profiles").update({"is_active": True, "activation_status": "active"}).eq("id", user_id).execute()
        return {"status": "success", "message": "ব্যবহারকারীকে সফলভাবে সচল ও অ্যাক্টিভ করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
def delete_user_account(user_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.auth.admin.delete_user(user_id)
        supabase.table("profiles").delete().eq("id", user_id).execute()
        return {"status": "success", "message": "ব্যবহারকারীর অ্যাকাউন্ট ও প্রোফাইল ডাটাবেজ থেকে চিরতরে ডিলিট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/withdrawals")
def get_pending_withdrawals(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("withdrawals")\
            .select("*, profiles!user_id(full_name)")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve-withdrawal/{withdrawal_id}")
def approve_withdrawal(withdrawal_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("withdrawals").update({"status": "approved"}).eq("id", withdrawal_id).execute()
        return {"status": "success", "message": "উইথড্রাল রিকোয়েস্টটি সফলভাবে অ্যাপ্রুভ ও পরিশোধ করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reject-withdrawal/{withdrawal_id}")
def reject_withdrawal(withdrawal_id: str, admin: dict = Depends(verify_admin)):
    try:
        withdraw_query = supabase.table("withdrawals").select("*").eq("id", withdrawal_id).single().execute()
        withdraw = withdraw_query.data
        if not withdraw:
            raise HTTPException(status_code=404, detail="রিকোয়েস্টটি পাওয়া যায়নি।")

        if withdraw['status'] != 'pending':
            return {"status": "info", "message": "এটি ইতিমধ্যে প্রসেস করা হয়েছে।"}

        user_id = withdraw['user_id']
        refund_amount = float(withdraw['amount'])

        user_profile = supabase.table("profiles").select("wallet_balance").eq("id", user_id).single().execute()
        if user_profile.data:
            current_bal = float(user_profile.data.get('wallet_balance', 0) or 0)
            supabase.table("profiles").update({"wallet_balance": current_bal + refund_amount}).eq("id", user_id).execute()
            supabase.table("withdrawals").update({"status": "rejected"}).eq("id", withdrawal_id).execute()

            return {"status": "success", "message": "রিকোয়েস্টটি বাতিল করা হয়েছে এবং টাকা ওয়ালেটে রিফান্ড করা হয়েছে।"}
        
        raise HTTPException(status_code=400, detail="ইউজার প্রোফাইল পাওয়া যায়নি।")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
