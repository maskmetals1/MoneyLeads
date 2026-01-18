#!/usr/bin/env python3
"""
Quick script to verify OpenAI API key is configured correctly
"""

from config import OPENAI_API_KEY, AI_PROVIDER, validate_config

print("=" * 60)
print("OpenAI API Key Verification")
print("=" * 60)

# Check AI Provider
print(f"\n✅ AI Provider: {AI_PROVIDER}")

# Check API Key
if OPENAI_API_KEY:
    print(f"✅ API Key loaded: Yes")
    print(f"✅ Key starts with: {OPENAI_API_KEY[:7]}...")
    print(f"✅ Key length: {len(OPENAI_API_KEY)} characters")
else:
    print(f"❌ API Key loaded: No")
    print(f"   Please add OPENAI_API_KEY to your .env file")

# Test ScriptGenerator
try:
    from script_generator import ScriptGenerator
    sg = ScriptGenerator()
    print(f"\n✅ ScriptGenerator initialized successfully")
    print(f"   Provider: {sg.provider}")
except ValueError as e:
    print(f"\n❌ ScriptGenerator error: {e}")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

# Validate full config
print(f"\n" + "=" * 60)
print("Full Configuration Validation")
print("=" * 60)
try:
    validate_config()
    print("\n✅ All configuration is valid!")
except ValueError as e:
    print(f"\n❌ Configuration errors found:")
    print(f"   {e}")

print("\n" + "=" * 60)

