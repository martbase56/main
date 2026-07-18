import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.database import supabase
from api.config import settings

router = APIRouter()

class ActivationRequestSchema(BaseModel):
    user_id: str
    payment_method: str = None
    sender_number: str = None   
    trx_id: str = None          

class ProfileUpdateSchema(BaseModel):
    full_name: str
    phone_number: str

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization হেডার অনুপস্থিত।")
    
    try:
        token = authorization.split(" ")[1]
        
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="টোকেনটি অবৈধ অথবা মেয়াদোত্তীর্ণ।")
            
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail="অবৈধ Authorization ফরম্যাট। 'Bearer <Token>' ব্যবহার করুন।")

@router.get("/config")
def get_supabase_config():
    activation_fee = 100.0
    ig_price = 15.0
    ig_notice = "ইনস্টাগ্রাম অ্যাকাউন্ট সাবমিট করুন। ২FA কী সচল থাকতে হবে।"
    fb_price = 20.0
    fb_notice = "ফেসবুক অ্যাকাউন্ট এবং কুকিজ সাবমিট করুন।"

    try:
        fee_query = supabase.table("system_settings").select("value").eq("key", "activation_fee").execute()
        if fee_query.data:
            activation_fee = float(fee_query.data[0]['value'])

        ig_price_query = supabase.table("system_settings").select("value").eq("key", "instagram_price").execute()
        if ig_price_query.data:
            ig_price = float(ig_price_query.data[0]['value'])

        ig_notice_query = supabase.table("system_settings").select("value").eq("key", "instagram_notice").execute()
        if ig_notice_query.data:
            ig_notice = ig_notice_query.data[0]['value']

        fb_price_query = supabase.table("system_settings").select("value").eq("key", "facebook_price").execute()
        if fb_price_query.data:
            fb_price = float(fb_price_query.data[0]['value'])

        fb_notice_query = supabase.table("system_settings").select("value").eq("key", "facebook_notice").execute()
        if fb_notice_query.data:
            fb_notice = fb_notice_query.data[0]['value']
            
    except Exception as e:
        print(f"Settings table error bypassed: {str(e)}")

    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY,
        "activation_fee": activation_fee,
        "instagram_price": ig_price,
        "instagram_notice": ig_notice,
        "facebook_price": fb_price,
        "facebook_notice": fb_notice
    }

@router.get("/profile/{user_id}")
def get_user_profile(user_id: str):
    try:
        query = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        if not query.data:
            raise HTTPException(status_code=404, detail="ব্যবহারকারী প্রোফাইল পাওয়া যায়নি।")
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/update-activity/{user_id}")
def update_activity(user_id: str):
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        supabase.table("profiles").update({"last_active_at": now_iso}).eq("id", user_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/referrals/{user_id}")
def get_and_evaluate_referrals(user_id: str):
    try:
        pending_query = supabase.table("referrals").select("*").eq("referrer_id", user_id).eq("status", "processing").execute()
        pending_referrals = pending_query.data
        
        for ref in pending_referrals:
            referred_id = ref['referred_id']
            created_at = datetime.fromisoformat(ref['created_at'].replace('Z', '+00:00'))
            expires_at = datetime.fromisoformat(ref['expires_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            profile_check = supabase.table("profiles").select("last_active_at", "is_active", "activation_status").eq("id", referred_id).single().execute()
            referred_profile = profile_check.data
            
            if referred_profile and (referred_profile['is_active'] == False or referred_profile['activation_status'] == 'banned'):
                supabase.table("referrals").update({"status": "failed"}).eq("id", ref['id']).execute()
                continue
            
            order_check = supabase.table("orders").select("id", count="exact").eq("placed_by", referred_id).eq("status", "delivered").execute()
            has_order = order_check.count > 0 if order_check.count is not None else False
            
            last_active = datetime.fromisoformat(referred_profile['last_active_at'].replace('Z', '+00:00'))
            is_active_session = (last_active - created_at).total_seconds() > 300
            
            if has_order or is_active_session:
                supabase.table("referrals").update({"status": "success"}).eq("id", ref['id']).execute()
                
                ref_profile = supabase.table("profiles").select("wallet_balance").eq("id", user_id).single().execute()
                current_bal = float(ref_profile.data.get('wallet_balance', 0) or 0)
                supabase.table("profiles").update({"wallet_balance": current_bal + 10.0}).eq("id", user_id).execute()
                
            elif now > expires_at:
                supabase.table("referrals").update({"status": "failed"}).eq("id", ref['id']).execute()
        
        all_referrals_query = supabase.table("referrals")\
            .select("*, profiles!referred_id(full_name, refer_code, is_active)")\
            .eq("referrer_id", user_id)\
            .execute()
            
        return all_referrals_query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
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
