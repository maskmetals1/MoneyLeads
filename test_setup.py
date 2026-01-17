#!/usr/bin/env python3
"""
Test script to verify Supabase setup is complete
"""

from supabase_client import SupabaseClient
from config import validate_config
import sys

def test_setup():
    """Test all components of the setup"""
    print("=" * 60)
    print("🧪 Testing Supabase Setup")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Test 1: Configuration
    print("1️⃣  Testing configuration...")
    try:
        validate_config()
        print("   ✅ Configuration valid")
    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        all_passed = False
    print()
    
    # Test 2: Supabase Connection
    print("2️⃣  Testing Supabase connection...")
    try:
        client = SupabaseClient()
        print("   ✅ Supabase client created")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        all_passed = False
        return all_passed
    print()
    
    # Test 3: Storage Buckets
    print("3️⃣  Testing storage buckets...")
    try:
        buckets = client.client.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        required = ["voiceovers", "renders", "scripts"]
        
        for req in required:
            if req in bucket_names:
                print(f"   ✅ Bucket '{req}' exists")
            else:
                print(f"   ❌ Bucket '{req}' missing")
                all_passed = False
    except Exception as e:
        print(f"   ❌ Error checking buckets: {e}")
        all_passed = False
    print()
    
    # Test 4: Database Tables
    print("4️⃣  Testing database tables...")
    try:
        jobs = client.get_all_jobs(limit=1)
        print("   ✅ video_jobs table exists and is accessible")
    except Exception as e:
        if "Could not find the table" in str(e):
            print("   ⚠️  video_jobs table not found")
            print("   📝 Please run the SQL schema in Supabase SQL Editor:")
            print("      https://supabase.com/dashboard/project/mdyayczcvpkbrdpdtkjb/sql/new")
            all_passed = False
        else:
            print(f"   ❌ Error: {e}")
            all_passed = False
    print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! Setup is complete.")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_setup()
    sys.exit(0 if success else 1)

