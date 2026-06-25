# config.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Gunakan string koneksi khusus Connection Pooling dari Supabase (Port 6543)
# Ini wajib untuk platform serverless seperti Vercel biar koneksi tidak putus-putus
DATABASE_URL = "postgresql://postgres:bZHVYNNibi5r9Mie@db.qwokowmwcfldqwjxpbfs.supabase.co:6543/postgres?sslmode=require"

def get_db_connection():
    try:
        # Menambahkan parameter connect_timeout agar Vercel tidak menggantung lama jika gagal
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, connect_timeout=5)
        return conn
    except Exception as e:
        print(f"Gagal konek ke database cloud: {e}")
        return None