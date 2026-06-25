# config.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# sslmode diganti menjadi disable agar bypass verifikasi sertifikat di server cloud Vercel
DATABASE_URL = "postgresql://postgres:bZHVYNNibi5r9Mie@db.qwokowmwcfldqwjxpbfs.supabase.co:6543/postgres?sslmode=disable"

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, connect_timeout=10)
        return conn
    except Exception as e:
        print(f"Gagal konek ke database cloud: {e}")
        return None