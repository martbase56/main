import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.database import supabase
from api.routers.admin import verify_admin

router = APIRouter()

class IGSubmitSchema(BaseModel):
    user_id: str
    username: str
    two_factor_key: str

@router.post("/submit")
def submit_instagram(data: IGSubmitSchema):
    try:
        user_check = supabase.table("profiles").select("role, is_active").eq("id", data.user_id).single().execute()
        if not user_check.data or not user_check.data['is_active']:
            raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাক্টিভ ব্যবহারকারীরাই টাস্ক সাবমিট করতে পারবেন।")

        payload = {
            "user_id": data.user_id,
            "username": data.username.strip().lower(),
            "two_factor_key": data.two_factor_key.strip()
        }

        supabase.table("instagram_submissions").insert(payload).execute()
        return {"status": "success", "message": "আপনার ইনস্টাগ্রাম অ্যাকাউন্টটি সফলভাবে সাবমিট হয়েছে এবং এটি যাচাইয়ের জন্য পেন্ডিং রয়েছে।"}
    except Exception as e:
        if "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="এই ইনস্টাগ্রাম ইউজারনেমটি ইতিপূর্বে সাবমিট করা হয়েছে!")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
def get_user_ig_history(user_id: str):
    try:
        query = supabase.table("instagram_submissions")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/submissions")
def get_pending_ig_submissions(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("instagram_submissions")\
            .select("*, profiles!user_id(full_name, phone_number)")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/approve/{submission_id}")
def approve_ig_submission(submission_id: str, admin: dict = Depends(verify_admin)):
    try:
        sub_query = supabase.table("instagram_submissions").select("*").eq("id", submission_id).single().execute()
        if not sub_query.data:
            raise HTTPException(status_code=404, detail="সাবমিশন আইডিটি খুঁজে পাওয়া যায়নি।")
        
        submission = sub_query.data
        if submission['status'] == 'approved':
            return {"status": "info", "message": "এটি ইতিমধ্যে অনুমোদিত হয়েছে।"}

        rate_query = supabase.table("system_settings").select("value").eq("key", "instagram_price").single().execute()
        rate = float(rate_query.data['value']) if rate_query.data else 15.0

        user_id = submission['user_id']
        user_profile = supabase.table("profiles").select("wallet_balance").eq("id", user_id).single().execute()
        
        if user_profile.data:
            current_bal = float(user_profile.data.get('wallet_balance', 0) or 0)
            
            supabase.table("profiles").update({"wallet_balance": current_bal + rate}).eq("id", user_id).execute()
            supabase.table("instagram_submissions").update({"status": "approved"}).eq("id", submission_id).execute()

            return {"status": "success", "message": f"অ্যাকাউন্ট সফলভাবে গৃহীত হয়েছে এবং ইউজারের ওয়ালেটে ৳{rate} ক্রেডিট করা হয়েছে।"}
        
        raise HTTPException(status_code=400, detail="ইউজার প্রোফাইল খুঁজে পাওয়া যায়নি।")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/reject/{submission_id}")
def reject_ig_submission(submission_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("instagram_submissions").update({"status": "rejected"}).eq("id", submission_id).execute()
        return {"status": "success", "message": "ইনস্টাগ্রাম অ্যাকাউন্টটি বাতিল/রিজেক্ট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
