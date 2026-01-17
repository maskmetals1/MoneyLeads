#!/usr/bin/env python3
"""
Execute SQL schema to create database tables
"""

from supabase import create_client
import requests

SUPABASE_URL = "https://mdyayczcvpkbrdpdtkjb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1keWF5Y3pjdnBrYnJkcGR0a2piIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODY4MjUwMCwiZXhwIjoyMDg0MjU4NTAwfQ.hsZXXFTzmKbGEpNzi1482nDEA4hy2GO7EK5oLot0p2U"

def run_sql():
    """Execute SQL schema using REST API"""
    print("📊 Executing SQL schema...")
    
    # Read SQL schema
    with open("supabase_schema.sql", "r") as f:
        sql = f.read()
    
    # Use Supabase REST API to execute SQL
    # Note: This requires using the PostgREST API or Management API
    # For now, we'll use a direct approach with the service role key
    
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Split SQL into individual statements
    statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
    
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Execute each statement
    for i, statement in enumerate(statements, 1):
        if not statement:
            continue
        
        # Skip comments
        if statement.startswith("--"):
            continue
        
        try:
            # Use rpc or direct SQL execution
            # Note: Supabase Python client doesn't support raw SQL directly
            # We need to use the REST API
            print(f"  Executing statement {i}/{len(statements)}...")
            
            # For CREATE TABLE and other DDL, we need to use the Management API
            # or execute via psql. Let's use a simpler approach - provide instructions
            pass
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
    
    print()
    print("⚠️  Direct SQL execution via Python client is limited.")
    print("   Please run the SQL schema in Supabase SQL Editor:")
    print(f"   https://supabase.com/dashboard/project/mdyayczcvpkbrdpdtkjb/sql/new")
    print()
    print("   Or use Supabase CLI:")
    print("   supabase db execute --file supabase_schema.sql")

if __name__ == "__main__":
    run_sql()

