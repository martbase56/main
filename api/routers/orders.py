# api/routers/orders.py (সম্পূর্ণ ও চূড়ান্ত কোড)
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.database import supabase
from api.routers.auth import get_current_user

router = APIRouter()

# --- ১. Pydantic ডেটা ভ্যালিডেশন স্কিমাস ---

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
    payment_details: dict = None          # {"sender_number": "...", "trx_id": "..."}
    order_note: str = None
    items: list[OrderItemSchema]          # কার্টের সমস্ত প্রোডাক্টের তালিকা
    collectable_amount: float             # কাস্টমার থেকে টোটাল কালেকশন (Discounts সহ)
    shipping_cost: float
    coupon_code: str = None
    coupon_discount: float = 0.0

class CouponValidateSchema(BaseModel):
    code: str
    order_amount: float


# --- ২. এন্ডপয়েন্ট: কুপন ভ্যালিডেশন ---
@router.post("/validate-coupon")
def validate_coupon(data: CouponValidateSchema):
    try:
        query = supabase.table("coupons").select("*").eq("code", data.code.upper()).eq("is_active", True).execute()
        if not query.data:
            raise HTTPException(status_code=404, detail="অবৈধ বা নিষ্ক্রিয় কুপন কোড।")
        
        coupon = query.data[0]
        if data.order_amount < float(coupon['min_order_amount']):
            raise HTTPException(status_code=400, detail=f"এই কুপনটি ব্যবহার করতে ন্যূনতম ৳{coupon['min_order_amount']} অর্ডারের প্রয়োজন।")
        
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
        # Pydantic items অবজেক্টকে JSON ফরম্যাটে রূপান্তর
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
