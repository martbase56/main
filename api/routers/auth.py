# api/routers/auth.py
import os
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from api.database import supabase
from api.config import settings

router = APIRouter()

# --- ১. Pydantic ডেটা ভ্যালিডেশন স্কিমাস ---

class ActivationRequestSchema(BaseModel):
    user_id: str
    payment_method: str = None  # 'bKash' অথবা 'Nagad'
    sender_number: str = None   # যে নম্বর থেকে টাকা পাঠানো হয়েছে
    trx_id: str = None          # ট্রানজেকশন আইডি

class ProfileUpdateSchema(BaseModel):
    full_name: str
    phone_number: str


# --- ২. সিকিউর টোকেন ভেরিফিকেশন ডিপেনডেন্সি (FastAPI JWT Dependency) ---

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization হেডার অনুপস্থিত।")
    
    try:
        # "Bearer <token>" ফরম্যাট থেকে টোকেন আলাদা করা
        token = authorization.split(" ")[1]
        
        # Supabase-এর মাধ্যমে টোকেনটি ভ্যালিড কিনা তা যাচাই করা
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="টোকেনটি অবৈধ অথবা মেয়াদোত্তীর্ণ।")
            
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail="অবৈধ Authorization ফরম্যাট। 'Bearer <Token>' ব্যবহার করুন।")


# --- ৩. ডাইনামিক এনভায়রনমেন্ট কনফিগ ডেলিভারি এন্ডপয়েন্ট ---
# এটি Vercel থেকে পাবলিক ক্রেডেনশিয়াল রিড করে ফ্রন্টএন্ডে সেফলি সাপ্লাই করবে

@router.get("/config")
def get_supabase_config():
    # Vercel Environment Variables থেকে মান নিয়ে ফ্রন্টএন্ডে পাঠানো
    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY
    }


# --- ৪. এন্ডপয়েন্ট: ব্যবহারকারীর প্রোফাইল তথ্য দেখা ---

@router.get("/profile/{user_id}")
def get_user_profile(user_id: str):
    try:
        query = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        if not query.data:
            raise HTTPException(status_code=404, detail="ব্যবহারকারী প্রোফাইল পাওয়া যায়নি।")
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৫. এন্ডপয়েন্ট: প্রোফাইল তথ্য আপডেট করা ---

@router.put("/profile/{user_id}")
def update_user_profile(user_id: str, data: ProfileUpdateSchema, current_user: dict = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="আপনি অন্যের প্রোফাইল পরিবর্তন করতে পারবেন না।")

    try:
        update_data = {
            "full_name": data.full_name,
            "phone_number": data.phone_number
        }
        query = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
        return {"status": "success", "message": "প্রোফাইল সফলভাবে আপডেট করা হয়েছে।", "data": query.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- ৬. এন্ডপয়েন্ট: অ্যাকাউন্ট অ্যাক্টিভেশন রিকোয়েস্ট সাবমিট ---

@router.post("/request-activation")
def request_activation(data: ActivationRequestSchema):
    try:
        # ডাইনামিক অ্যাক্টিভেশন ফি চেক করা
        fee_query = supabase.table("system_settings").select("value").eq("key", "activation_fee").single().execute()
        activation_fee = float(fee_query.data['value']) if fee_query.data else 0.0

        # ফি যদি ০ (ফ্রি) হয়, তবে সরাসরি অ্যাক্টিভ করে দেওয়া হবে
        if activation_fee == 0:
            supabase.table("profiles").update({
                "is_active": True,
                "activation_status": "active"
            }).eq("id", data.user_id).execute()
            
            return {"status": "success", "message": "আপনার অ্যাকাউন্টটি সফলভাবে সক্রিয় করা হয়েছে (ফ্রি অ্যাক্টিভেশন)।"}

        # ফি যদি ০-এর বেশি হয়, তবে পেমেন্ট ডিটেইলস ভ্যালিডেশন
        if not data.payment_method or not data.sender_number or not data.trx_id:
            raise HTTPException(status_code=400, detail="পেমেন্ট গেটওয়ে, sender নম্বর এবং Trx ID প্রদান করা বাধ্যতামূলক।")

        # অ্যাক্টিভেশন রিকোয়েস্ট ডাটাবেজে রেকর্ড করা
        request_payload = {
            "user_id": data.user_id,
            "payment_method": data.payment_method,
            "sender_number": data.sender_number,
            "trx_id": data.trx_id,
            "amount": activation_fee,
            "status": "pending"
        }

        supabase.table("activation_requests").insert(request_payload).execute()
        
        # ইউজারের প্রোফাইল অ্যাক্টিভেশন স্ট্যাটাস 'pending' করা
        supabase.table("profiles").update({"activation_status": "pending"}).eq("id", data.user_id).execute()
        
        return {"status": "success", "message": "আপনার পেমেন্ট ভেরিফিকেশন রিকোয়েস্টটি সফলভাবে জমা হয়েছে।"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail="এই Trx ID টি ইতিপূর্বে ব্যবহৃত হয়েছে অথবা ভুল ডেটা দেওয়া হয়েছে।")


# --- ৭. অ্যাডমিন এন্ডপয়েন্ট: পেন্ডিং রিকোয়েস্ট অ্যাপ্রুভ (অনুমোদন) করা ---

@router.post("/admin/approve-activation/{request_id}")
def approve_activation(request_id: str, admin_user: dict = Depends(get_current_user)):
    # সিকিউরিটি চেক: অ্যাডমিন ভ্যালিডেশন
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাডমিনরাই এই অপারেশন করতে পারবেন।")

    # রিকোয়েস্টটি খুঁজে বের করা
    req_query = supabase.table("activation_requests").select("*").eq("id", request_id).single().execute()
    req_data = req_query.data
    if not req_data:
        raise HTTPException(status_code=404, detail="রিকোয়েস্টটি পাওয়া যায়নি।")

    if req_data['status'] == 'approved':
        return {"status": "info", "message": "এটি ইতিমধ্যেই অনুমোদিত হয়েছে।"}

    # রিকোয়েস্ট স্ট্যাটাস এবং ইউজারের প্রোফাইল আপডেট
    supabase.table("activation_requests").update({"status": "approved"}).eq("id", request_id).execute()
    supabase.table("profiles").update({
        "is_active": True,
        "activation_status": "active"
    }).eq("id", req_data['user_id']).execute()

    return {"status": "success", "message": "ইউজার অ্যাকাউন্টটি সফলভাবে সক্রিয় করা হয়েছে।"}


# --- ৮. অ্যাডমিন এন্ডপয়েন্ট: পেন্ডিং রিকোয়েস্ট রিজেক্ট (বাতিল) করা ---

@router.post("/admin/reject-activation/{request_id}")
def reject_activation(request_id: str, admin_user: dict = Depends(get_current_user)):
    # সিকিউরিটি চেক: অ্যাডমিন ভ্যালিডেশন
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাডমিনরাই এই অপারেশন করতে পারবেন।")

    # রিকোয়েস্টটি খুঁজে বের করা
    req_query = supabase.table("activation_requests").select("*").eq("id", request_id).single().execute()
    req_data = req_query.data
    if not req_data:
        raise HTTPException(status_code=404, detail="রিকোয়েস্টটি পাওয়া যায়নি।")

    # স্ট্যাটাস রিজেক্টেড করা
    supabase.table("activation_requests").update({"status": "rejected"}).eq("id", request_id).execute()
    supabase.table("profiles").update({"activation_status": "rejected"}).eq("id", req_data['user_id']).execute()

    return {"status": "success", "message": "আবেদনটি বাতিল করা হয়েছে।"}
