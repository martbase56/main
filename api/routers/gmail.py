# api/routers/gmail.py
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from api.database import supabase
from api.routers.admin import verify_admin

router = APIRouter()

# --- ১. Pydantic ডেটা ভ্যালিডেশন স্কিমাস ---
class BatchCreateSchema(BaseModel):
    passcode: str
    price_per_mail: float
    closing_at: datetime

class GmailSubmitSchema(BaseModel):
    reseller_id: str
    gmail_address: str

class CSVProcessSchema(BaseModel):
    rejected_emails: List[str]  # রিজেক্টেড মেইলের তালিকা


# --- ২. এন্ডপয়েন্ট: সচল ওপেন ব্যাচ তথ্য খোঁজা (রিসেলারদের জন্য) ---
@router.get("/active-batch")
def get_active_batch():
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        # বর্তমানে ওপেন এবং ক্লোজিং টাইম পার হয়নি এমন ব্যাচ খোঁজা
        query = supabase.table("gmail_batches")\
            .select("*")\
            .eq("status", "open")\
            .gt("closing_at", now_iso)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
            
        if not query.data:
            return {"status": "inactive", "message": "বর্তমানে কোনো একটিভ জিমেইল ব্যাচ চালু নেই।"}
        return {"status": "active", "batch": query.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৩. এন্ডপয়েন্ট: রিসেলার কর্তৃক জিমেইল সাবমিট করা ---
@router.post("/submit")
def submit_gmail(data: GmailSubmitSchema):
    try:
        # ক. রিসেলার ভেরিফিকেশন
        res_check = supabase.table("profiles").select("role, is_active").eq("id", data.reseller_id).single().execute()
        if not res_check.data or res_check.data['role'] != 'reseller' or not res_check.data['is_active']:
            raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র একটিভ রিসেলাররাই জিমেইল সাবমিট করতে পারবেন।")

        # খ. ওপেন ব্যাচ চেক
        now_iso = datetime.now(timezone.utc).isoformat()
        batch_query = supabase.table("gmail_batches").select("*").eq("status", "open").gt("closing_at", now_iso).order("created_at", desc=True).limit(1).execute()
        if not batch_query.data:
            raise HTTPException(status_code=400, detail="দুঃখিত, বর্তমানে জিমেইল সাবমিট করার কোনো সচল ব্যাচ নেই।")
        
        active_batch = batch_query.data[0]

        # গ. সাবমিশন ডেটাবেজে সংরক্ষণ (ইউনিক কনস্ট্রেইন্ট চেক)
        submission_payload = {
            "batch_id": active_batch['id'],
            "reseller_id": data.reseller_id,
            "gmail_address": data.gmail_address.strip().lower()
        }

        supabase.table("gmail_submissions").insert(submission_payload).execute()
        return {"status": "success", "message": "আপনার জিমেইলটি সফলভাবে সাবমিট হয়েছে এবং এটি যাচাইয়ের জন্য পেন্ডিং রয়েছে।"}
    except Exception as e:
        if "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="এই জিমেইলটি ইতিপূর্বে এই ব্যাচে সাবমিট করা হয়েছে!")
        raise HTTPException(status_code=500, detail=str(e))


# --- ৪. এন্ডপয়েন্ট: রিসেলারের নিজস্ব সাবমিশন হিস্ট্রি দেখা ---
@router.get("/history/{reseller_id}")
def get_reseller_gmail_history(reseller_id: str):
    try:
        query = supabase.table("gmail_submissions")\
            .select("*, gmail_batches(batch_num, price_per_mail)")\
            .eq("reseller_id", reseller_id)\
            .order("created_at", desc=True)\
            .execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== এডমিন এন্ডপয়েন্টসমূহ ====================

# --- ৫. এন্ডপয়েন্ট: এডমিন কর্তৃক নতুন ব্যাচ চালু করা ---
@router.post("/admin/create-batch")
def create_new_batch(data: BatchCreateSchema, admin: dict = Depends(verify_admin)):
    try:
        # পূর্বের ওপেন করা সব ব্যাচ স্বয়ংক্রিয়ভাবে রিভিউইংয়ে পাঠানো
        supabase.table("gmail_batches").update({"status": "reviewing"}).eq("status", "open").execute()

        payload = {
            "passcode": data.passcode,
            "price_per_mail": data.price_per_mail,
            "closing_at": data.closing_at.isoformat(),
            "status": "open"
        }
        query = supabase.table("gmail_batches").insert(payload).execute()
        return {"status": "success", "message": "নতুন জিমেইল ব্যাচ সফলভাবে চালু করা হয়েছে।", "batch": query.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৬. এন্ডপয়েন্ট: সকল ব্যাচের তালিকা দেখা ---
@router.get("/admin/batches")
def get_all_batches(admin: dict = Depends(verify_admin)):
    try:
        query = supabase.table("gmail_batches").select("*").order("created_at", desc=True).execute()
        return query.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৭. এন্ডপয়েন্ট: CSV/রিজেক্টেড লিস্ট প্রসেস এবং অটো-অ্যাপ্রুভাল ও ব্যালেন্স ডিস্ট্রিবিউশন ---
@router.post("/admin/process-review/{batch_id}")
def process_batch_review(batch_id: str, data: CSVProcessSchema, admin: dict = Depends(verify_admin)):
    try:
        # ক. ব্যাচের বিবরণী আনা
        batch_query = supabase.table("gmail_batches").select("*").eq("id", batch_id).single().execute()
        if not batch_query.data:
            raise HTTPException(status_code=404, detail="ব্যাচটি খুঁজে পাওয়া যায়নি।")
        batch = batch_query.data
        price = float(batch['price_per_mail'])

        # খ. এই ব্যাচের সকল পেন্ডিং সাবমিশন নিয়ে আসা
        submissions_query = supabase.table("gmail_submissions").select("*").eq("batch_id", batch_id).eq("status", "pending").execute()
        submissions = submissions_query.data

        if not submissions:
            return {"status": "info", "message": "এই ব্যাচে কোনো পেন্ডিং জিমেইল রিভিউ করার জন্য নেই।"}

        rejected_set = set(email.strip().lower() for email in data.rejected_emails)

        # গ. সাবমিশন প্রসেস লুপ
        for sub in submissions:
            sub_id = sub['id']
            res_id = sub['reseller_id']
            email_addr = sub['gmail_address'].strip().lower()

            if email_addr in rejected_set:
                # রিজেক্টেড মেইলগুলোর স্ট্যাটাস 'rejected' করা
                supabase.table("gmail_submissions").update({"status": "rejected"}).eq("id", sub_id).execute()
            else:
                # বাকি সব মেইল স্বয়ংক্রিয়ভাবে 'approved' করা
                supabase.table("gmail_submissions").update({"status": "approved"}).eq("id", sub_id).execute()

                # সাকসেসফুল মেইলের টাকা রিসেলারের মেইন ব্যালেন্সে ও জিমেইল কাউন্টারে যোগ করা [1.1.2]
                reseller_profile = supabase.table("profiles").select("wallet_balance, gmail_sells").eq("id", res_id).single().execute()
                if reseller_profile.data:
                    current_bal = float(reseller_profile.data.get('wallet_balance', 0) or 0)
                    current_sells = int(reseller_profile.data.get('gmail_sells', 0) or 0)

                    # টাকা ও সাকসেস টার্গেট আপডেট
                    supabase.table("profiles").update({
                        "wallet_balance": current_bal + price,
                        "gmail_sells": current_sells + 1 # ৫00 টাকা লকড বোনাস কাউন্টার ডাইনামিকালি ১ বাড়বে!
                    }).eq("id", res_id).execute()

        # ঘ. ব্যাচটি ক্লোজ/কমপ্লিট করা
        supabase.table("gmail_batches").update({"status": "completed"}).eq("id", batch_id).execute()

        return {"status": "success", "message": "ব্যাচের জিমেইল রিভিউ সফলভাবে সম্পন্ন হয়েছে এবং রিসেলারদের ওয়ালেটে টাকা ক্রেডিট করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
