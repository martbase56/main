from supabase import create_client, Client
from api.config import settings

if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "Database configuration is incomplete. "
        "Please ensure both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set."
    )

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
