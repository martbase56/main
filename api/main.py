# api/main.py
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.routers import auth, products, orders, admin 

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


# --- ১. ফেইল-সেফ স্ট্যাটিক ফাইল ফাইন্ডার (Vercel Container Root Checker) ---
def get_html_response(filename: str):
    # Vercel-এর সার্ভারলেস কন্টেইনারের রুট ডিরেক্টরি (/var/task) খুঁজে বের করা
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # রুট ডিরেক্টরিতে ফাইল চেক করা
    file_path = os.path.join(base_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    # Vercel-এর ভেতরে কপি হওয়া 'public' ফোল্ডারের ফাইল চেক করা
    public_file_path = os.path.join(base_dir, "public", filename)
    if os.path.exists(public_file_path):
        return FileResponse(public_file_path)
        
    raise HTTPException(status_code=404, detail=f"দুঃখিত, '{filename}' ফাইলটি আপনার সার্ভারে খুঁজে পাওয়া যায়নি।")


# --- ২. স্ট্যাটিক ফাইল রাউটারসমূহ (যা এপিআই এবং 404 এরর দূর করবে) ---

@app.get("/")
def read_index():
    return get_html_response("index.html")

@app.get("/login")
def read_login():
    return get_html_response("login.html")

@app.get("/signup")
def read_signup():
    return get_html_response("signup.html")

@app.get("/signup/reseller")
def read_signup_reseller():
    return get_html_response("signup-reseller.html")

@app.get("/dashboard/admin")
def read_admin():
    return get_html_response("dashboard/admin.html")

@app.get("/dashboard/add-product")
def read_add_product():
    return get_html_response("dashboard/add-product.html")


# --- ৩. ব্যাকএন্ড এপিআই রাউটারসমূহ রেজিস্টার করা ---
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Panel"])


# এপিআই রুট চেক করার জন্য বেসিক টেস্ট এন্ডপয়েন্ট
@app.get("/api")
def read_api_root():
    return {
        "status": "success",
        "message": "MartBaseBD API is running successfully!",
        "version": "1.0.0"
    }
