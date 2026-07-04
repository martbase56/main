# api/database.py
from supabase import create_client, Client
from api.config import settings

# ডাটাবেজ কনফিগারেশন মিসিং থাকলে অ্যাপ্লিকেশন রান হতে বাধা দেবে (নিরাপত্তার জন্য)
if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "Database configuration is incomplete. "
        "Please ensure both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set."
    )

# গ্লোবাল Supabase ক্লায়েন্ট তৈরি
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
