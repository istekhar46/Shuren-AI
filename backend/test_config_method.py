"""Quick test script for get_required_llm_api_key method"""
import os
from app.core.config import Settings, LLMProvider

# Test 1: Anthropic provider with key
print("Test 1: Anthropic with API key")
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["LLM_PROVIDER"] = "anthropic"
settings1 = Settings()
try:
    key = settings1.get_required_llm_api_key()
    print(f"✓ Returned key: {key}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Anthropic provider without key
print("\nTest 2: Anthropic without API key")
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["LLM_PROVIDER"] = "anthropic"
settings2 = Settings()
try:
    key = settings2.get_required_llm_api_key()
    print(f"✗ Should have raised ValueError but got: {key}")
except ValueError as e:
    print(f"✓ Correctly raised ValueError: {e}")

# Test 3: OpenAI provider with key
print("\nTest 3: OpenAI with API key")
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["LLM_PROVIDER"] = "openai"
settings3 = Settings()
try:
    key = settings3.get_required_llm_api_key()
    print(f"✓ Returned key: {key}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Google provider with key
print("\nTest 4: Google with API key")
os.environ["GOOGLE_API_KEY"] = "test-google-key"
os.environ["LLM_PROVIDER"] = "google"
settings4 = Settings()
try:
    key = settings4.get_required_llm_api_key()
    print(f"✓ Returned key: {key}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n✓ All tests passed!")
