# api/routers/admin.py
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Header
from api.database import supabase
from api.routers.auth import get_current_user  # JWT টোকেন দিয়ে লগইন চেক করার জন্য

router = APIRouter()

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
        # ক. মোট ইউজার সংখ্যা (Total Users)
        total_users_query = supabase.table("profiles").select("id", count="exact").execute()
        total_users_count = total_users_query.count if total_users_query.count is not None else 0

        # খ. আজকের তারিখের শুরু (ISO Format in UTC)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_iso = today_start.isoformat()

        # গ. আজকের নতুন ইউজার সংখ্যা
        today_users_query = supabase.table("profiles").select("id", count="exact").gte("created_at", today_start_iso).execute()
        today_users_count = today_users_query.count if today_users_query.count is not None else 0

        # ঘ. আজকের মোট অর্ডার ও টাকার পরিমাণ
        today_orders_query = supabase.table("orders").select("total_cost", count="exact").gte("created_at", today_start_iso).execute()
        today_orders_count = today_orders_query.count if today_orders_query.count is not None else 0
        
        today_orders_data = today_orders_query.data
        today_amount = sum(float(order['total_cost']) for order in today_orders_data) if today_orders_data else 0.0

        # (সংশোধিত অংশ) 'todayUsers' টাইপো পরিবর্তন করে 'today_users_count' করা হয়েছে
        return {
            "total_users": total_users_count,
            "today_users": today_users_count,
            "today_orders": today_orders_count,
            "today_amount": today_amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"স্ট্যাটস ডাটা লোডে সমস্যা: {str(e)}")


# --- ৩. এন্ডপয়েন্ট: পেন্ডিং অ্যাক্টিভেশন রিকোয়েস্ট তালিকা ---
@router.get("/activation-requests")
def get_pending_activation_requests(admin: dict = Depends(verify_admin)):
    try:
        # profiles টেবিলের সাথে যুক্ত করে পেন্ডিং রিকোয়েস্ট ও ইউজারের নাম রিড করা
        query = supabase.table("activation_requests")\
            .select("*, profiles(full_name)")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"পেন্ডিং রিকোয়েস্ট লোডে সমস্যা: {str(e)}")


# --- ৪. এন্ডপয়েন্ট: পেন্ডিং অ্যাক্টিভেশন অনুমোদন করা ---
@router.post("/approve-activation/{request_id}")
def approve_activation(request_id: str, admin: dict = Depends(verify_admin)):
    req_query = supabase.table("activation_requests").select("*").eq("id", request_id).single().execute()
    req_data = req_query.data
    if not req_data:
        raise HTTPException(status_code=404, detail="রিকোয়েস্টটি পাওয়া যায়নি।")

    if req_data['status'] == 'approved':
        return {"status": "info", "message": "এটি ইতিমধ্যেই অনুমোদিত হয়েছে।"}

    try:
        supabase.table("activation_requests").update({"status": "approved"}).eq("id", request_id).execute()
        supabase.table("profiles").update({
            "is_active": True,
            "activation_status": "active"
        }).eq("id", req_data['user_id']).execute()

        return {"status": "success", "message": "ইউজার অ্যাকাউন্টটি সফলভাবে সক্রিয় করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- ৫. এন্ডপয়েন্ট: পেন্ডিং অ্যাক্টিভেশন বাতিল করা ---
@router.post("/reject-activation/{request_id}")
def reject_activation(request_id: str, admin: dict = Depends(verify_admin)):
    req_query = supabase.table("activation_requests").select("*").eq("id", request_id).single().execute()
    req_data = req_query.data
    if not req_data:
        raise HTTPException(status_code=404, detail="রিকোয়েস্টটি পাওয়া যায়নি।")

    try:
        supabase.table("activation_requests").update({"status": "rejected"}).eq("id", request_id).execute()
        supabase.table("profiles").update({"activation_status": "rejected"}).eq("id", req_data['user_id']).execute()

        return {"status": "success", "message": "আবেদনটি সফলভাবে বাতিল করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
