# api/config.py
import os
from dotenv import load_dotenv

# লোকাল ডেভেলপমেন্টের জন্য .env ফাইল লোড করা (Vercel-এ এটি স্বয়ংক্রিয়ভাবে সিস্টেম থেকে রিড হবে)
load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # ডেভেলপমেন্টের সুবিধার্থে কোনো কি বাদ পড়লে কনসোলে ওয়ার্নিং দেখাবে
    def __init__(self):
        if not self.SUPABASE_URL:
            print("⚠️ Warning: 'SUPABASE_URL' is not set in environment variables.")
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            print("⚠️ Warning: 'SUPABASE_SERVICE_ROLE_KEY' is not set in environment variables.")

settings = Settings()
