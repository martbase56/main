# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# routers ফোল্ডার থেকে সকল মডুলার রাউটার ইম্পোর্ট করা হলো
from api.routers import auth, products, orders, admin 

app = FastAPI(
    title="MartBaseBD Premium API Platform",
    description="E-commerce and Dropshipping platform API managed securely with Supabase.",
    version="1.0.0"
)

# CORS পলিসি কনফিগারেশন (যাতে ফ্রন্টএন্ড থেকে এপিআই কল করার সময় ব্লক না হয়)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # প্রোডাকশনে আপনার নির্দিষ্ট Vercel ডোমেইন অ্যাড্রেস দেবেন (যেমন: https://yourdomain.vercel.app)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# প্রতিটি মডুলার রাউটারকে তাদের নির্দিষ্ট পাথ প্রিফিক্স এবং ট্যাগসহ যুক্ত করা হলো
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Panel"])


# এপিআই রুট চেক করার জন্য বেসিক টেস্ট এন্ডপয়েন্ট
@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "MartBaseBD API is running successfully!",
        "version": "1.0.0"
    }
