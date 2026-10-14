"""Tiny read-only query so the free Supabase project never counts as inactive (free projects pause after ~7 idle days)."""
import os, sys
import psycopg

url = os.environ.get("SUPABASE_DB_URL", "")
if not url:
    sys.exit("SUPABASE_DB_URL not set")
with psycopg.connect(url, connect_timeout=20) as conn:
    row = conn.execute("select now(), (select count(*) from information_schema.tables where table_schema in ('public','hub','n8n'))").fetchone()
print(f"OK   supabase reachable at {row[0]} ({row[1]} tables in public/hub/n8n)")
