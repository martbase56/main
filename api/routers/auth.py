# api/routers/auth.py
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.database import supabase
from api.config import settings

router = APIRouter()

# --- ১. Pydantic ডেটা ভ্যালিডেশন স্কিমাস ---

class ActivationRequestSchema(BaseModel):
    user_id: str
    payment_method: str = None  # 'bKash' অথবা 'Nagad'
    sender_number: str = None   
    trx_id: str = None          

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

# api/routers/auth.py এর ৩ নম্বর এন্ডপয়েন্টটি পরিবর্তন করে নিন:

# --- ৩. ডাইনামিক এনভায়রনমেন্ট কনফিগ ডেলিভারি এন্ডপয়েন্ট (অ্যাক্টিভেশন ফিসহ) ---
@router.get("/config")
def get_supabase_config():
    # ডাইনামিক অ্যাক্টিভেশন ফি বের করা
    fee_query = supabase.table("system_settings").select("value").eq("key", "activation_fee").single().execute()
    activation_fee = float(fee_query.data['value']) if fee_query.data else 0.0

    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY,
        "activation_fee": activation_fee  # এপিআই রেসপন্সে ফি যুক্ত করা হলো
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
        fee_query = supabase.table("system_settings").select("value").eq("key", "activation_fee").single().execute()
        activation_fee = float(fee_query.data['value']) if fee_query.data else 0.0

        if activation_fee == 0:
            supabase.table("profiles").update({
                "is_active": True,
                "activation_status": "active"
            }).eq("id", data.user_id).execute()
            
            return {"status": "success", "message": "আপনার অ্যাকাউন্টটি সফলভাবে সক্রিয় করা হয়েছে (ফ্রি অ্যাক্টিভেশন)।"}

        if not data.payment_method or not data.sender_number or not data.trx_id:
            raise HTTPException(status_code=400, detail="পেমেন্ট গেটওয়ে, sender নম্বর এবং Trx ID প্রদান করা বাধ্যতামূলক।")

        request_payload = {
            "user_id": data.user_id,
            "payment_method": data.payment_method,
            "sender_number": data.sender_number,
            "trx_id": data.trx_id,
            "amount": activation_fee,
            "status": "pending"
        }

        supabase.table("activation_requests").insert(request_payload).execute()
        supabase.table("profiles").update({"activation_status": "pending"}).eq("id", data.user_id).execute()
        
        return {"status": "success", "message": "আপনার পেমেন্ট ভেরিফিকেশন রিকোয়েস্টটি সফলভাবে জমা হয়েছে।"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail="এই Trx ID টি ইতিপূর্বে ব্যবহৃত হয়েছে অথবা ভুল ডেটা দেওয়া হয়েছে।")


# --- ৭. এন্ডপয়েন্ট: রিসেলার ড্যাশবোর্ড ভিজিটের সময় অ্যাক্টিভেশন টাইমস্ট্যাম্প আপডেট করা ---

@router.post("/update-activity/{user_id}")
def update_activity(user_id: str):
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        supabase.table("profiles").update({"last_active_at": now_iso}).eq("id", user_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# api/routers/auth.py এর শুধুমাত্র রেফারেল এন্ডপয়েন্ট অংশটি পরিবর্তন করুন:

# --- ৮. এন্ডপয়েন্ট: পেন্ডিং রেফারেল মূল্যায়ন ও রেফারেল তালিকা দেখা (ব্যানড ফিল্টার সহ) ---
@router.get("/referrals/{user_id}")
def get_and_evaluate_referrals(user_id: str):
    try:
        # ক. প্রসেসিং অবস্থায় থাকা রেফারেলগুলো ভেরিফাই করা
        pending_query = supabase.table("referrals").select("*").eq("referrer_id", user_id).eq("status", "processing").execute()
        pending_referrals = pending_query.data
        
        for ref in pending_referrals:
            referred_id = ref['referred_id']
            created_at = datetime.fromisoformat(ref['created_at'].replace('Z', '+00:00'))
            expires_at = datetime.fromisoformat(ref['expires_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            # নতুন সচলতা ও ব্যান চেক
            profile_check = supabase.table("profiles").select("last_active_at", "is_active", "activation_status").eq("id", referred_id).single().execute()
            referred_profile = profile_check.data
            
            # (গুরুত্বপূর্ণ ফিক্স) ইউজার যদি ব্যান (Banned) হয়ে থাকেন, তবে রেফারেল সরাসরি 'failed' হবে [1.1.2]
            if referred_profile and (referred_profile['is_active'] == False or referred_profile['activation_status'] == 'banned'):
                supabase.table("referrals").update({"status": "failed"}).eq("id", ref['id']).execute()
                continue # লুপের পরবর্তী রিকোর্ডে চলে যাবে
            
            # ১. কাস্টমার কোনো সফল অর্ডার করেছে কিনা চেক
            order_check = supabase.table("orders").select("id", count="exact").eq("placed_by", referred_id).eq("status", "delivered").execute()
            has_order = order_check.count > 0 if order_check.count is not None else False
            
            # ২. ড্যাশবোর্ডে সচল ছিল কিনা চেক (লাস্ট একটিভ টাইম রেজিস্ট্রেশন টাইমের ৫ মিনিট পর কিনা)
            last_active = datetime.fromisoformat(referred_profile['last_active_at'].replace('Z', '+00:00'))
            is_active_session = (last_active - created_at).total_seconds() > 300 # ৫ মিনিটের বেশি ড্যাশবোর্ডে ছিল
            
            # কন্ডিশন ম্যাচ করলে রেফারার ১০ টাকা পাবে এবং রেফারেল সাকসেস হবে [1.1.2]
            if has_order or is_active_session:
                # রেফারেল সফল করা
                supabase.table("referrals").update({"status": "success"}).eq("id", ref['id']).execute()
                
                # রেফারারের ওয়ালেটে ১০ টাকা যোগ করা [1.1.2]
                ref_profile = supabase.table("profiles").select("wallet_balance").eq("id", user_id).single().execute()
                current_bal = float(ref_profile.data.get('wallet_balance', 0) or 0)
                supabase.table("profiles").update({"wallet_balance": current_bal + 10.0}).eq("id", user_id).execute()
                
            elif now > expires_at:
                # ৩৬ ঘণ্টা পার হয়ে গেলে এবং কোনো কাজ না করলে ফেইল্ড
                supabase.table("referrals").update({"status": "failed"}).eq("id", ref['id']).execute()
        
        # খ. রেফারারের রেফারেল তালিকার লাইভ আপডেট নিয়ে আসা
        all_referrals_query = supabase.table("referrals")\
            .select("*, profiles!referred_id(full_name, refer_code, is_active)")\
            .eq("referrer_id", user_id)\
            .execute()
            
        return all_referrals_query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

# --- ৯. অ্যাডমিন এন্ডপয়েন্ট: পেন্ডিং রিকোয়েস্ট অ্যাপ্রুভ করা ---

@router.post("/admin/approve-activation/{request_id}")
def approve_activation(request_id: str, admin_user: dict = Depends(get_current_user)):
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাডমিনরাই এই অপারেশন করতে পারবেন।")

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


# --- ১০. অ্যাডমিন এন্ডপয়েন্ট: পেন্ডিং রিকোয়েস্ট রিজেক্ট করা ---

@router.post("/admin/reject-activation/{request_id}")
def reject_activation(request_id: str, admin_user: dict = Depends(get_current_user)):
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাডমিনরাই এই অপারেশন করতে পারবেন।")

    req_query = supabase.table("activation_requests").select("*").eq("id", request_id).single().execute()
    req_data = req_query.data
    if not req_data:
        raise HTTPException(status_code=404, detail="রিকোয়েস্টটি পাওয়া যায়নি।")

    supabase.table("activation_requests").update({"status": "rejected"}).eq("id", request_id).execute()
    supabase.table("profiles").update({"activation_status": "rejected"}).eq("id", req_data['user_id']).execute()

    return {"status": "success", "message": "আবেদনটি বাতিল করা হয়েছে।"}
