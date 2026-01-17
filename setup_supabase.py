#!/usr/bin/env python3
"""
Script to set up Supabase database and storage buckets
"""

import os
from supabase import create_client, Client
from pathlib import Path

# Supabase credentials
SUPABASE_URL = "https://mdyayczcvpkbrdpdtkjb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1keWF5Y3pjdnBrYnJkcGR0a2piIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODY4MjUwMCwiZXhwIjoyMDg0MjU4NTAwfQ.hsZXXFTzmKbGEpNzi1482nDEA4hy2GO7EK5oLot0p2U"

def setup_database():
    """Create database tables using SQL"""
    print("📊 Setting up database tables...")
    
    # Read SQL schema
    schema_path = Path(__file__).parent / "supabase_schema.sql"
    with open(schema_path, 'r') as f:
        sql = f.read()
    
    # Note: We can't execute SQL directly via Python client easily
    # User needs to run this in Supabase SQL Editor
    print("⚠️  Please run the SQL schema manually:")
    print(f"   1. Go to: https://supabase.com/dashboard/project/mdyayczcvpkbrdpdtkjb/sql/new")
    print(f"   2. Copy contents of: {schema_path}")
    print(f"   3. Paste and run in SQL Editor")
    print()
    
    return True

def setup_storage_buckets():
    """Create storage buckets"""
    print("🗂️  Setting up storage buckets...")
    
    client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    buckets = [
        {"name": "voiceovers", "public": True},
        {"name": "renders", "public": True},
        {"name": "scripts", "public": True}
    ]
    
    for bucket in buckets:
        try:
            # Check if bucket exists
            try:
                result = client.storage.get_bucket(bucket["name"])
                print(f"  ✅ Bucket '{bucket['name']}' already exists")
            except:
                # Create bucket
                result = client.storage.create_bucket(
                    bucket["name"],
                    options={"public": bucket["public"]}
                )
                print(f"  ✅ Created bucket '{bucket['name']}' (public: {bucket['public']})")
        except Exception as e:
            print(f"  ⚠️  Error with bucket '{bucket['name']}': {e}")
    
    return True

def test_connection():
    """Test Supabase connection"""
    print("🔌 Testing Supabase connection...")
    
    try:
        client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Test database connection
        result = client.table("video_jobs").select("id").limit(1).execute()
        print("  ✅ Database connection successful")
        
        # Test storage connection
        buckets = client.storage.list_buckets()
        print(f"  ✅ Storage connection successful ({len(buckets)} buckets)")
        
        return True
    except Exception as e:
        print(f"  ❌ Connection test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 Supabase Setup Script")
    print("=" * 60)
    print()
    
    # Setup storage buckets
    setup_storage_buckets()
    print()
    
    # Setup database (instructions)
    setup_database()
    print()
    
    # Test connection
    if test_connection():
        print()
        print("✅ Setup complete!")
        print()
        print("Next steps:")
        print("  1. Run the SQL schema in Supabase SQL Editor")
        print("  2. Update .env file with your API keys")
        print("  3. Test the worker: python worker.py")
    else:
        print()
        print("⚠️  Some setup steps may need manual intervention")

if __name__ == "__main__":
    main()

