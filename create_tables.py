#!/usr/bin/env python3
"""
Create database tables using Supabase Python client
Since raw SQL execution isn't available via REST API, we'll create tables programmatically
"""

from supabase import create_client
import json

SUPABASE_URL = "https://mdyayczcvpkbrdpdtkjb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1keWF5Y3pjdnBrYnJkcGR0a2piIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODY4MjUwMCwiZXhwIjoyMDg0MjU4NTAwfQ.hsZXXFTzmKbGEpNzi1482nDEA4hy2GO7EK5oLot0p2U"

def create_tables_via_web():
    """Provide instructions for creating tables via web interface"""
    print("=" * 60)
    print("📊 Database Setup Instructions")
    print("=" * 60)
    print()
    print("Supabase doesn't allow raw SQL execution via REST API for security.")
    print("Please create the tables using the SQL Editor:")
    print()
    print("1. Open SQL Editor:")
    print("   https://supabase.com/dashboard/project/mdyayczcvpkbrdpdtkjb/sql/new")
    print()
    print("2. Copy and paste the entire contents of: supabase_schema.sql")
    print()
    print("3. Click 'Run' to execute")
    print()
    print("4. Verify tables were created:")
    print("   https://supabase.com/dashboard/project/mdyayczcvpkbrdpdtkjb/editor")
    print()
    print("You should see:")
    print("  ✅ video_jobs table")
    print("  ✅ youtube_videos table")
    print()

def test_connection():
    """Test if tables exist"""
    print("🔌 Testing connection...")
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Try to query video_jobs table
        try:
            result = client.table("video_jobs").select("id").limit(1).execute()
            print("  ✅ video_jobs table exists!")
            return True
        except Exception as e:
            if "Could not find the table" in str(e):
                print("  ⚠️  video_jobs table not found - please run SQL schema")
                return False
            else:
                raise
        
    except Exception as e:
        print(f"  ❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    create_tables_via_web()
    
    if test_connection():
        print("✅ Database is ready!")
    else:
        print("⚠️  Please create tables using SQL Editor first")

