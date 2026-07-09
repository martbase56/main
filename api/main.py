# api/main.py (সকল ৭টি রাউটার ইম্পোর্ট সহ চূড়ান্ত কোড)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# (সংশোধিত) routers ফোল্ডার থেকে সকল ৭টি মডুলার রাউটার ইম্পোর্ট করা হলো (কোনো নেম-এরর এড়াতে)
from api.routers import auth, products, orders, admin, gmail, instagram, telegram, facebook

app = FastAPI(
    title="MerketBaseBD Premium API Platform",
    description="E-commerce, Dropshipping, Task and Social Promotion Management Hub.",
    version="1.2.0"
)

# CORS পলিসি কনফিগারেশন (ফ্রন্টএন্ড কানেক্টিভিটি সুরক্ষায়)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # প্রোডাকশনে আপনার নির্দিষ্ট Vercel ডোমেইন অ্যাড্রেস দেবেন
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# প্রতিটি মডুলার রাউটার রেজিস্টার করা হলো
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Panel"])
app.include_router(gmail.router, prefix="/api/gmail", tags=["Gmail Tasks"])
app.include_router(instagram.router, prefix="/api/instagram", tags=["Instagram Tasks"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["Telegram Services"])
app.include_router(facebook.router, prefix="/api/facebook", tags=["Facebook Tasks"])

# এপিআই রুট চেক করার জন্য বেসিক টেস্ট এন্ডপয়েন্ট
@app.get("/api")
def read_api_root():
    return {
        "status": "success",
        "message": "MerketBaseBD API is running successfully!",
        "version": "1.2.0"
    }
