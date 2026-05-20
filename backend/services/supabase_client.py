from supabase import create_client, Client
from backend.config import get_settings

settings = get_settings()

_client: Client = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def get_supabase_admin() -> Client:
    """Service role client — bypasses RLS. Falls back to the anon/publishable client if unset."""
    key = (settings.supabase_service_key or "").strip()
    if key:
        return create_client(settings.supabase_url, key)
    return get_supabase()
