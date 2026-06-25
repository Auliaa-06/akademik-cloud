# config.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# USERNAME: postgres (murni, tanpa titik atau project ID)
# HOST: db.qwokowmwcfldqwjxpbfs.supabase.co
# PORT: 5432
# Ganti PASWORD_HASIL_RESET_ANDA dengan password database Anda

DATABASE_URL = "postgresql://postgres:bZHVYNNibi5r9Mie@db.qwokowmwcfldqwjxpbfs.supabase.co:5432/postgres?sslmode=require"

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Gagal konek ke database cloud: {e}")
        return None