# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.database import supabase

app = FastAPI(title="MartBaseBD Premium API Platform")

# CORS পলিসি কনফিগারেশন
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ডাইনামিক ক্যাটাগরি ও প্রোডাক্ট এপিআই হোমপেজের জন্য ---

@app.get("/api/home/categories")
def get_home_categories():
    # ডাটাবেজ থেকে সকল ক্যাটাগরি লোড করা
    query = supabase.table("categories").select("*").execute()
    return query.data

@app.get("/api/home/products")
def get_home_products():
    # ড্যাশবোর্ডে প্রদর্শনের জন্য সাম্প্রতিক ৩০টি প্রোডাক্ট লোড করা
    query = supabase.table("products").select("*").limit(30).order("created_at", desc=True).execute()
    return query.data
