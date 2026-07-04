# api/routers/orders.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.database import supabase
from api.routers.auth import get_current_user

router = APIRouter()

class OrderSchema(BaseModel):
    user_id: str
    product_id: str
    quantity: int
    customer_name: str
    customer_phone: str
    delivery_address: str
    collectable_amount: float = 0

@router.post("/place")
def place_order(order: OrderSchema):
    # ১. ব্যবহারকারীর প্রোফাইল থেকে রোল চেক
    user_query = supabase.table("profiles").select("role").eq("id", order.user_id).single().execute()
    user_profile = user_query.data
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_role = user_profile['role']

    # ২. প্রোডাক্টের মূল্য তালিকা চেক
    product_query = supabase.table("products").select("*").eq("id", order.product_id).single().execute()
    product = product_query.data
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    regular_price = float(product['regular_price'])
    reseller_price = float(product['reseller_price'])

    # ৩. লাভ ও মূল্যের হিসাবনিকাশ
    total_cost = 0.0
    reseller_profit = 0.0

    if user_role == 'reseller':
        total_cost = reseller_price * order.quantity
        if order.collectable_amount > total_cost:
            reseller_profit = order.collectable_amount - total_cost
        else:
            order.collectable_amount = total_cost
            reseller_profit = 0.0
    else:
        total_cost = regular_price * order.quantity
        order.collectable_amount = total_cost
        reseller_profit = 0.0

    # ৪. ডাটাবেজে নতুন অর্ডার রেকর্ড তৈরি
    order_payload = {
        "placed_by": order.user_id,
        "user_role": user_role,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "delivery_address": order.delivery_address,
        "total_cost": total_cost,
        "collectable_amount": order.collectable_amount,
        "reseller_profit": reseller_profit,
        "status": "pending"
    }

    inserted_order = supabase.table("orders").insert(order_payload).execute()
    
    return {
        "status": "success",
        "message": "Order placed successfully!",
        "order": inserted_order.data
    }

@router.post("/admin/update-status/{order_id}")
def update_order_status(order_id: str, new_status: str, admin_user: dict = Depends(get_current_user)):
    # এডমিন সিকিউরিটি চেক
    admin_check = supabase.table("profiles").select("role").eq("id", admin_user.id).single().execute()
    if not admin_check.data or admin_check.data['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update order status.")

    # ১. অর্ডারের বর্তমান তথ্য ডাটাবেজ থেকে আনা
    order_query = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    order = order_query.data
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order['status'] == 'delivered':
        raise HTTPException(status_code=400, detail="This order is already delivered and profit was credited.")

    # ২. অর্ডারের স্ট্যাটাস আপডেট করা
    supabase.table("orders").update({"status": new_status}).eq("id", order_id).execute()

    # ৩. স্ট্যাটাস যদি 'delivered' হয় এবং অর্ডারটি যদি কোনো রিসেলার প্লেস করে থাকে
    if new_status == 'delivered' and order['user_role'] == 'reseller':
        reseller_id = order['placed_by']
        profit = float(order['reseller_profit'])

        if profit > 0:
            # রিসেলারের বর্তমান ব্যালেন্স নিয়ে আসা
            res_query = supabase.table("profiles").select("wallet_balance").eq("id", reseller_id).single().execute()
            current_balance = float(res_query.data['wallet_balance']) if res_query.data else 0.0
            
            # নতুন ব্যালেন্স হিসাব করে আপডেট করা
            new_balance = current_balance + profit
            supabase.table("profiles").update({"wallet_balance": new_balance}).eq("id", reseller_id).execute()

            return {
                "status": "success", 
                "message": f"Order status updated. Profit BDT {profit} credited to reseller wallet."
            }

    return {"status": "success", "message": f"Order status updated to {new_status}."}
