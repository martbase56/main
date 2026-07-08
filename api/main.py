# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, products, orders, admin, gmail

app = FastAPI(
    title="MartBaseBD Premium API Platform",
    description="E-commerce and Dropshipping platform API managed securely with Supabase.",
    version="1.0.0"
)

# CORS পলিসি কনফিগারেশন
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# এপিআই রুট চেক করার জন্য বেসিক টেস্ট এন্ডপয়েন্ট
@app.get("/api")
def read_api_root():
    return {
        "status": "success",
        "message": "MartBaseBD API is running successfully!",
        "version": "1.0.0"
    }
