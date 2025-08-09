"""Simple test script to verify API keys work."""

import os
import asyncio
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_openai():
    """Test OpenAI API key (skips if no key)."""
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OpenAI API works!'"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API: WORKING")
        print(f"   Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API: FAILED - {e}")
        return False

@pytest.mark.asyncio
async def test_anthropic():
    """Test Anthropic API key (skips if no key)."""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Say 'Anthropic API works!'"}],
            max_tokens=10
        )
        
        print("✅ Anthropic API: WORKING")
        print(f"   Response: {response.content[0].text}")
        return True
    except Exception as e:
        print(f"❌ Anthropic API: FAILED - {e}")
        return False

async def main():
    print("🔑 Testing API Keys...")
    print("=" * 40)
    
    openai_works = await test_openai()
    anthropic_works = await test_anthropic()
    
    print("\n📊 Summary:")
    if openai_works or anthropic_works:
        print("🎉 At least one API is working! You can run AI Design Theater.")
        if openai_works and anthropic_works:
            print("🌟 Both APIs work - you'll get the full Dreamer vs Cost Cutter experience!")
        elif openai_works:
            print("💡 Only OpenAI works - both personalities will use OpenAI.")
        else:
            print("💡 Only Anthropic works - both personalities will use Anthropic.")
    else:
        print("❌ No APIs are working. Please check your keys in .env file.")

if __name__ == "__main__":
    asyncio.run(main())