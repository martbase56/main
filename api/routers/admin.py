# api/routers/admin.py
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from api.database import supabase
from api.routers.auth import get_current_user

router = APIRouter()

def verify_admin(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.id
        admin_check = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        if not admin_check.data or admin_check.data['role'] != 'admin':
            raise HTTPException(status_code=403, detail="অনুমতি নেই।")
        return current_user
    except Exception:
        raise HTTPException(status_code=403, detail="এডমিন ভেরিফিকেশন ব্যর্থ হয়েছে।")

@router.get("/stats")
def get_dashboard_stats(admin: dict = Depends(verify_admin)):
    try:
        total_users_query = supabase.table("profiles").select("id", count="exact").execute()
        total_users_count = total_users_query.count if total_users_query.count is not None else 0

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_iso = today_start.isoformat()

        today_users_query = supabase.table("profiles").select("id", count="exact").gte("created_at", today_start_iso).execute()
        today_users_count = today_users_query.count if today_users_query.count is not None else 0

        today_orders_query = supabase.table("orders").select("total_cost", count="exact").gte("created_at", today_start_iso).execute()
        today_orders_count = today_orders_query.count if today_orders_query.count is not None else 0
        
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
            .select("*, profiles(full_name)")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- (নতুন এপিআই) এন্ডপয়েন্ট: এডমিন অর্ডারের তালিকা দেখতে পারবেন ---
@router.get("/orders")
def get_all_orders(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("orders")\
            .select("*, profiles(full_name)")\
            .order("created_at", { "ascending": False })\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
