# config.py

SUPABASE_URL = "https://qwokowmwcfldqwjxpbfs.supabase.co"
# GANTI TULISAN DI BAWAH INI DENGAN ANON KEY KAMU YANG PANJANG:
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3b2tvd213Y2ZsZHF3anhwYmZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzOTczMzUsImV4cCI6MjA5Nzk3MzMzNX0.Mros9ocmjz1BSlvFdx1aJf8vZX-EE_ZenTQmbe4ehdk"

def get_supabase_client():
    """Menggunakan teknik lazy import agar Vercel tidak crash saat inisialisasi awal"""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def query_supabase_api(table_name, filters=None):
    try:
        supabase_client = get_supabase_client()
        query = supabase_client.table(table_name).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        res = query.execute()
        return res.data
    except Exception as e:
        print(f"Error fetching {table_name}: {e}")
        return []