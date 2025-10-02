"""
Test file to verify our APIs are working
Run this before building agents to ensure everything is connected
"""

import asyncio
from typing import Dict, Any
from openai import OpenAI
from tavily import TavilyClient
import sys
import os

# Add parent directory to path so we can import our config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

def test_openai_api() -> bool:
    """Test if OpenAI API is working"""
    print("\n🧪 Testing OpenAI API...")
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Simple test prompt
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "user", "content": "Say 'API test successful' in exactly 3 words"}
            ],
            max_tokens=10,
            temperature=0
        )
        
        result = response.choices[0].message.content
        print(f"   Response: {result}")
        print("   ✅ OpenAI API is working!")
        return True
        
    except Exception as e:
        print(f"   ❌ OpenAI API Error: {str(e)}")
        return False

def test_tavily_api() -> bool:
    """Test if Tavily Search API is working"""
    print("\n🔍 Testing Tavily API...")
    
    try:
        # Initialize Tavily client
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # Simple search test
        response = client.search(
            query="What is LangGraph?",
            max_results=2
        )
        
        # Check if we got results
        if response.get('results'):
            print(f"   Found {len(response['results'])} results")
            print(f"   First result: {response['results'][0]['title'][:50]}...")
            print("   ✅ Tavily API is working!")
            return True
        else:
            print("   ❌ No search results returned")
            return False
            
    except Exception as e:
        print(f"   ❌ Tavily API Error: {str(e)}")
        return False

def check_costs():
    """Display API costs information"""
    print("\n💰 API Costs (for reference):")
    print("   • OpenAI GPT-4o-mini: ~$0.15 per 1M input tokens")
    print("   • Tavily: 1000 searches/month free")
    print("   • Estimated project cost: < $1 for full testing")

def main():
    """Run all API tests"""
    print("=" * 50)
    print("🚀 MULTI-AGENT RESEARCH ASSISTANT - API TESTS")
    print("=" * 50)
    
    # First validate settings
    if not settings.validate():
        print("\n⚠️  Please add your API keys to the .env file")
        return
    
    # Run tests
    openai_ok = test_openai_api()
    tavily_ok = test_tavily_api()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print("=" * 50)
    
    if openai_ok and tavily_ok:
        print("🎉 All APIs working! Ready for Phase 2")
        check_costs()
    else:
        print("⚠️  Some APIs failed. Please check:")
        if not openai_ok:
            print("   • Your OpenAI API key")
        if not tavily_ok:
            print("   • Your Tavily API key (get free at https://tavily.com)")

if __name__ == "__main__":
    main()