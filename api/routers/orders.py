# api/routers/orders.py
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.database import supabase
from api.routers.auth import get_current_user

router = APIRouter()

# --- ১. Pydantic ডেটা ভ্যালিডেশন স্কিমাস (সুপার-কম্প্যাটিবল টাইপিং) ---

class OrderItemSchema(BaseModel):
    product_id: str
    quantity: int
    price: float

class OrderCreateSchema(BaseModel):
    user_id: str
    customer_name: str
    customer_phone: str
    delivery_address: str
    payment_method: str = "COD"
    payment_details: Optional[Dict[str, Any]] = None
    order_note: Optional[str] = None
    items: List[OrderItemSchema]                    # কার্টের প্রোডাক্ট তালিকা
    collectable_amount: float
    shipping_cost: float
    coupon_code: Optional[str] = None
    coupon_discount: float = 0.0

class CouponValidateSchema(BaseModel):
    code: str
    order_amount: float


# --- ২. এন্ডপয়েন্ট: কুপন ভ্যালিডেশন ---
@router.post("/validate-coupon")
def validate_coupon(data: CouponValidateSchema):
    try:
        # সচল কুপন কোডটি ডাটাবেজ থেকে খুঁজে বের করা
        query = supabase.table("coupons")\
            .select("*")\
            .eq("code", data.code.upper())\
            .eq("is_active", True)\
            .execute()
            
        if not query.data:
            raise HTTPException(status_code=404, detail="অবৈধ বা নিষ্ক্রিয় কুপন কোড।")
        
        coupon = query.data[0]
        
        # ন্যূনতম অর্ডার অ্যামাউন্ট চেক
        if data.order_amount < float(coupon['min_order_amount']):
            raise HTTPException(
                status_code=400, 
                detail=f"এই কুপনটি ব্যবহার করতে ন্যূনতম ৳{coupon['min_order_amount']} অর্ডারের প্রয়োজন।"
            )
        
        # ডিসকাউন্ট হিসাব করা
        discount = 0.0
        if coupon['discount_type'] == 'percentage':
            discount = data.order_amount * (float(coupon['discount_value']) / 100.0)
        else:
            discount = float(coupon['discount_value'])
            
        return {
            "status": "success",
            "discount_amount": discount,
            "discount_type": coupon['discount_type'],
            "discount_value": coupon['discount_value']
        }
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))


# --- ৩. এন্ডপয়েন্ট: মাল্টি-আইটেম অর্ডার প্লেসিং ---
@router.post("/place")
def place_order(order: OrderCreateSchema):
    try:
        # ক. ব্যবহারকারীর রোল চেক করা
        user_query = supabase.table("profiles").select("role").eq("id", order.user_id).single().execute()
        if not user_query.data:
            raise HTTPException(status_code=404, detail="ব্যবহারকারী পাওয়া যায়নি।")
        user_role = user_query.data['role']

        # খ. প্রতিটি প্রোডাক্টের রিসেলার কস্ট গণনা করা (লাভ হিসাবের জন্য)
        total_reseller_cost = 0.0
        for item in order.items:
            product_query = supabase.table("products").select("reseller_price").eq("id", item.product_id).single().execute()
            if product_query.data:
                total_reseller_cost += float(product_query.data['reseller_price']) * item.quantity

        # গ. রিসেলার লাভ নির্ধারণ করা
        reseller_profit = 0.0
        if user_role == 'reseller':
            # রিসেলারের লাভ = (কালেকশন অ্যামাউন্ট - শিপিং খরচ) - রিসেলার পাইকারি দাম
            reseller_profit = (order.collectable_amount - order.shipping_cost) - total_reseller_cost
            if reseller_profit < 0:
                reseller_profit = 0.0

        # ঘ. ডাটাবেজে অর্ডার ইনসার্ট করা
        serialized_items = [item.dict() for item in order.items]

        order_payload = {
            "placed_by": order.user_id,
            "user_role": user_role,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "payment_method": order.payment_method,
            "payment_details": order.payment_details,
            "order_note": order.order_note,
            "items": serialized_items,
            "total_cost": total_reseller_cost if user_role == 'reseller' else order.collectable_amount,
            "collectable_amount": order.collectable_amount,
            "shipping_cost": order.shipping_cost,
            "coupon_code": order.coupon_code.upper() if order.coupon_code else None,
            "coupon_discount": order.coupon_discount,
            "reseller_profit": reseller_profit,
            "status": "pending"
        }

        new_order = supabase.table("orders").insert(order_payload).execute()
        return {"status": "success", "message": "আপনার অর্ডারটি সফলভাবে সাবমিট হয়েছে!", "order": new_order.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ৪. এন্ডপয়েন্ট: এডমিন কর্তৃক অর্ডার স্ট্যাটাস আপডেট (৫টি কাস্টম স্ট্যাটাস) ---
@router.post("/admin/update-status/{order_id}")
def update_order_status(order_id: str, new_status: str, admin_user: dict = Depends(get_current_user)):
    # এডমিন সিকিউরিটি চেক
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="দুঃখিত, শুধুমাত্র অ্যাডমিনরাই অর্ডার স্ট্যাটাস আপডেট করতে পারবেন।")

    # ক. অর্ডারের বর্তমান তথ্য ডাটাবেজ থেকে আনা
    order_query = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    order = order_query.data
    if not order:
        raise HTTPException(status_code=404, detail="অর্ডারটি খুঁজে পাওয়া যায়নি।")

    if order['status'] == 'delivered':
        raise HTTPException(status_code=400, detail="এই অর্ডারটি ইতিমধ্যে ডেলিভারি করা হয়েছে এবং প্রফিট যোগ করা হয়েছে।")

    # খ. অর্ডারের স্ট্যাটাস আপডেট করা ( pending, accepted, shipped, delivered, cancelled )
    try:
        supabase.table("orders").update({"status": new_status}).eq("id", order_id).execute()

        # গ. স্ট্যাটাস যদি ডেলিভারি ('delivered') হয় এবং অর্ডারটি যদি কোনো রিসেলার প্লেস করে থাকে
        if new_status == 'delivered' and order['user_role'] == 'reseller':
            reseller_id = order['placed_by']
            profit = float(order.get('reseller_profit', 0) or 0)

            if profit > 0:
                # রিসেলারের বর্তমান হোল্ড ব্যালেন্স নিয়ে আসা
                res_query = supabase.table("profiles").select("hold_balance").eq("id", reseller_id).single().execute()
                current_hold = float(res_query.data.get('hold_balance', 0) or 0)
                
                # প্রফিট সরাসরি হোল্ড ব্যালেন্সে (Hold Balance) জমা করা
                new_hold = current_hold + profit
                supabase.table("profiles").update({"hold_balance": new_hold}).eq("id", reseller_id).execute()

                return {
                    "status": "success", 
                    "message": f"অর্ডার ডেলিভারি সফল! রিসেলারের হোল্ড ব্যালেন্সে ৳{profit} প্রফিট যোগ করা হয়েছে।"
                }

        return {"status": "success", "message": f"অর্ডারের স্ট্যাটাস সফলভাবে '{new_status}' এ পরিবর্তন করা হয়েছে।"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"স্ট্যাটাস আপডেট ব্যর্থ: {str(e)}")


# --- ৫. এন্ডপয়েন্ট: রিসেলার কর্তৃক হোল্ড ব্যালেন্স মেইন ওয়ালেটে স্থানান্তর ---
@router.post("/transfer-hold/{user_id}")
def transfer_hold_balance(user_id: str):
    try:
        # ক. প্রফাইল ও ট্র্যাকিং ডাটা আনা
        profile_query = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        if not profile_query.data:
            raise HTTPException(status_code=404, detail="রিসেলার প্রোফাইল পাওয়া যায়নি।")
        
        profile = profile_query.data
        hold_balance = float(profile.get('hold_balance', 0) or 0)
        wallet_balance = float(profile.get('wallet_balance', 0) or 0)
        gmail_sells = int(profile.get('gmail_sells', 0) or 0)

        # খ. সফল ডেলিভারি করা অর্ডারের সংখ্যা ফেচ
        orders_query = supabase.table("orders").select("id", count="exact").eq("placed_by", user_id).eq("status", "delivered").execute()
        delivered_count = orders_query.count if orders_query.count is not None else 0

        # গ. সফল রেফারেল সংখ্যা ফেচ
        referrals_query = supabase.table("referrals").select("id", count="exact").eq("referrer_id", user_id).eq("status", "success").execute()
        referral_count = referrals_query.count if referrals_query.count is not None else 0

        # ঘ. লক্ষ্যমাত্রা সীমানানির্ধারণ (১০টি ডেলিভারি, ১০টি জিমেইল সেল, ৪টি রেফারেল)
        orders_target = 10
        gmail_target = 10
        referral_target = 4

        target_met = (delivered_count >= orders_target) and (gmail_sells >= gmail_target) and (referral_count >= referral_target)

        if not target_met:
            raise HTTPException(
                status_code=400, 
                detail=f"লক্ষ্যমাত্রা এখনও পূরণ হয়নি! ডেলিভারি: {delivered_count}/{orders_target}, জিমেইল: {gmail_sells}/{gmail_target}, রেফারেল: {referral_count}/{referral_target}"
            )

        if hold_balance <= 0:
            raise HTTPException(status_code=400, detail="উইথড্র বা ট্রান্সফার করার মতো কোনো হোল্ড ব্যালেন্স নেই।")

        # ঙ. ব্যালেন্স ট্রান্সফার করা (হোল্ড টু মেইন ওয়ালেট)
        new_wallet_balance = wallet_balance + hold_balance
        supabase.table("profiles").update({
            "wallet_balance": new_wallet_balance,
            "hold_balance": 0.0
        }).eq("id", user_id).execute()

        return {
            "status": "success",
            "message": f"সাফল্য! আপনার হোল্ড ব্যালেন্স ৳{hold_balance} সফলভাবে মেইন ব্যালেন্সে ট্রান্সফার করা হয়েছে।"
        }
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))
