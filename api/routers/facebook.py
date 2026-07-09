# api/routers/facebook.py
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.database import supabase
from api.routers.admin import verify_admin

router = APIRouter()

# --- Pydantic ডেটা ভ্যালিডেশন স্কিমাস ---
class FBSubmitSchema(BaseModel):
    user_id: str
    fb_uid: str
    cookies: str

# --- ১. এন্ডপয়েন্ট: কাস্টমার কর্তৃক ফেসবুক অ্যাকাউন্ট সাবমিট ---
@router.post("/submit")
def submit_facebook(data: FBSubmitSchema):
    try:
        # ইউজার চেক
        user_check = supabase.table("profiles").select("role, is_active").eq("id", data.user_id).single().execute()
        if not user_check.data or not user_check.data['is_active']:
            raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাক্টিভ ব্যবহারকারীরাই ফেসবুক টাস্ক সাবমিট করতে পারবেন।")

        # ডাটাবেজে সাবমিশন ইনসার্ট
        payload = {
            "user_id": data.user_id,
            "fb_uid": data.fb_uid.strip(),
            "cookies": data.cookies.strip()
        }

        supabase.table("facebook_submissions").insert(payload).execute()
        return {"status": "success", "message": "আপনার ফেসবুক অ্যাকাউন্ট বিবরণ সফলভাবে সাবমিট হয়েছে এবং এটি যাচাইয়ের জন্য পেন্ডিং রয়েছে।"}
    except Exception as e:
        if "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="এই ফেসবুক UID টি ইতিপূর্বে সাবমিট করা হয়েছে!")
        raise HTTPException(status_code=500, detail=str(e))


# --- ২. এন্ডপয়েন্ট: ব্যবহারকারীর নিজস্ব ফেসবুক সাবমিশন হিস্ট্রি ---
@router.get("/history/{user_id}")
def get_user_fb_history(user_id: str):
    try:
        query = supabase.table("facebook_submissions")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== এডমিন এন্ডপয়েন্টসমূহ ====================

# --- ৩. এন্ডপয়েন্ট: এডমিন কর্তৃক পেন্ডিং ফেসবুক তালিকা দেখা ---
@router.get("/admin/submissions")
def get_pending_fb_submissions(admin: dict = Depends(verify_admin)):
    try:
        # profiles টেবিলের সাথে জয়েন করে পেন্ডিং লিস্ট ভিউ করা
        query = supabase.table("facebook_submissions")\
            .select("*, profiles!user_id(full_name, phone_number)")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৪. এন্ডপয়েন্ট: ফেসবুক টাস্ক অনুমোদন এবং ওয়ালেটে ব্যালেন্স যোগ করা ---
@router.post("/admin/approve/{submission_id}")
def approve_fb_submission(submission_id: str, admin: dict = Depends(verify_admin)):
    try:
        # ক. সাবমিশন রেকর্ড খোঁজা
        sub_query = supabase.table("facebook_submissions").select("*").eq("id", submission_id).single().execute()
        if not sub_query.data:
            raise HTTPException(status_code=404, detail="সাবমিশন আইডিটি খুঁজে পাওয়া যায়নি।")
        
        submission = sub_query.data
        if submission['status'] == 'approved':
            return {"status": "info", "message": "এটি ইতিমধ্যে অনুমোদিত হয়েছে।"}

        # খ. সেটিংস থেকে ফেসবুক অর্ডারের রেট নিয়ে আসা
        rate_query = supabase.table("system_settings").select("value").eq("key", "facebook_price").single().execute()
        rate = float(rate_query.data['value']) if rate_query.data else 20.0

        # গ. ইউজারের ওয়ালেটে টাকা এড করা
        user_id = submission['user_id']
        user_profile = supabase.table("profiles").select("wallet_balance").eq("id", user_id).single().execute()
        
        if user_profile.data:
            current_bal = float(user_profile.data.get('wallet_balance', 0) or 0)
            
            # ওয়ালেটে টাকা যোগ করা
            supabase.table("profiles").update({"wallet_balance": current_bal + rate}).eq("id", user_id).execute()
            # সাবমিশন অ্যাপ্রুভড মার্ক করা
            supabase.table("facebook_submissions").update({"status": "approved"}).eq("id", submission_id).execute()

            return {"status": "success", "message": f"অ্যাকাউন্ট সফলভাবে গৃহীত হয়েছে এবং ইউজারের ওয়ালেটে ৳{rate} ক্রেডিট করা হয়েছে।"}
        
        raise HTTPException(status_code=400, detail="ইউজার প্রোফাইল খুঁজে পাওয়া যায়নি।")
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))


# --- ৫. এন্ডপয়েন্ট: ফেসবুক টাস্ক রিজেক্ট করা ---
@router.post("/admin/reject/{submission_id}")
def reject_fb_submission(submission_id: str, admin: dict = Depends(verify_admin)):
    try:
        supabase.table("facebook_submissions").update({"status": "rejected"}).eq("id", submission_id).execute()
        return {"status": "success", "message": "ফেসবুক সাবমিশনটি বাতিল/রিজেক্ট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
