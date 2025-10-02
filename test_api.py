# backend/test_api.py
"""
Test client for the FastAPI server
Run this to verify all endpoints are working correctly
"""

import requests
import json
import asyncio
import websockets
from datetime import datetime
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class APITestClient:
    """Test client for the Multi-Agent Research API"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def test_root(self):
        """Test root endpoint"""
        print("\n" + "="*50)
        print("1️⃣ Testing Root Endpoint")
        print("="*50)
        
        response = self.session.get(f"{self.base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint working")
            print(f"   Name: {data['name']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    
    def test_health(self):
        """Test health check endpoint"""
        print("\n" + "="*50)
        print("2️⃣ Testing Health Check")
        print("="*50)
        
        response = self.session.get(f"{self.base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   APIs configured:")
            for api, configured in data['apis_configured'].items():
                status = "✅" if configured else "❌"
                print(f"      {status} {api}")
            print(f"   Cache stats: {data['cache_stats']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    
    def test_research(self, query: str = "What is FastAPI?", use_cache: bool = True):
        """Test research endpoint"""
        print("\n" + "="*50)
        print("3️⃣ Testing Research Endpoint")
        print("="*50)
        print(f"   Query: {query}")
        print(f"   Use cache: {use_cache}")
        
        payload = {
            "query": query,
            "use_cache": use_cache,
            "report_type": "summary"
        }
        
        print("   ⏳ Sending request (this may take 30-40 seconds)...")
        start_time = datetime.now()
        
        response = self.session.post(
            f"{self.base_url}/api/research",
            json=payload
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Research completed in {duration:.1f} seconds")
            print(f"   Success: {data['success']}")
            print(f"   Cached: {data['cached']}")
            if data.get('report'):
                print(f"   Report length: {len(data['report'])} characters")
                print(f"   Report preview:")
                print(f"   {data['report'][:200]}...")
            if data.get('metadata'):
                print(f"   Metadata:")
                for key, value in data['metadata'].items():
                    print(f"      - {key}: {value}")
            return True
        else:
            print(f"❌ Research failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    
    def test_cache_stats(self):
        """Test cache statistics endpoint"""
        print("\n" + "="*50)
        print("4️⃣ Testing Cache Statistics")
        print("="*50)
        
        response = self.session.get(f"{self.base_url}/api/cache/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cache stats retrieved")
            for key, value in data.items():
                print(f"   {key}: {value}")
            return True
        else:
            print(f"❌ Cache stats failed: {response.status_code}")
            return False
    
    async def test_websocket(self, query: str = "What is WebSocket?"):
        """Test WebSocket endpoint for real-time updates"""
        print("\n" + "="*50)
        print("5️⃣ Testing WebSocket Connection")
        print("="*50)
        print(f"   Query: {query}")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                print("✅ WebSocket connected")
                
                # Send query
                await websocket.send(json.dumps({"query": query}))
                print("   📤 Query sent")
                
                # Receive updates
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "status":
                        print(f"   📍 Status: {data.get('message')}")
                    elif data.get("type") == "progress":
                        print(f"   ⏳ Progress: {data.get('step')} - {data.get('message')} ({data.get('progress'):.0f}%)")
                    elif data.get("type") == "complete":
                        print(f"   ✅ Complete! Cached: {data.get('cached')}")
                        if data.get("report"):
                            print(f"   Report length: {len(data['report'])} characters")
                        break
                    elif data.get("type") == "error":
                        print(f"   ❌ Error: {data.get('error')}")
                        break
                
                return True
        except Exception as e:
            print(f"❌ WebSocket test failed: {str(e)}")
            return False
    
    def test_invalid_request(self):
        """Test error handling with invalid request"""
        print("\n" + "="*50)
        print("6️⃣ Testing Error Handling")
        print("="*50)
        
        # Test with query too short
        payload = {
            "query": "Hi",  # Too short (min 5 chars)
            "use_cache": True
        }
        
        response = self.session.post(
            f"{self.base_url}/api/research",
            json=payload
        )
        
        if response.status_code == 422:  # Validation error
            print(f"✅ Validation error handled correctly")
            error = response.json()
            print(f"   Error details: {error.get('detail', [{}])[0].get('msg', 'Unknown')}")
            return True
        else:
            print(f"❌ Expected validation error, got: {response.status_code}")
            return False
    
    def test_cache_behavior(self):
        """Test cache hit/miss behavior"""
        print("\n" + "="*50)
        print("7️⃣ Testing Cache Behavior")
        print("="*50)
        
        test_query = "What is caching in web applications?"
        
        # First request (should be cache miss)
        print("   First request (expecting cache miss)...")
        response1 = self.session.post(
            f"{self.base_url}/api/research",
            json={"query": test_query, "use_cache": True}
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"   ✅ First request: Cached = {data1['cached']} (should be False)")
            
            # Second request (should be cache hit)
            print("   Second request (expecting cache hit)...")
            response2 = self.session.post(
                f"{self.base_url}/api/research",
                json={"query": test_query, "use_cache": True}
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"   ✅ Second request: Cached = {data2['cached']} (should be True)")
                
                # Verify reports are identical
                if data1['report'] == data2['report']:
                    print("   ✅ Reports match (cache working correctly)")
                    return True
                else:
                    print("   ❌ Reports don't match (cache issue)")
                    return False
        
        return False

def run_all_tests():
    """Run all API tests"""
    print("\n" + "🚀"*20)
    print("   MULTI-AGENT RESEARCH API - TEST SUITE")
    print("🚀"*20)
    
    client = APITestClient()
    results = []
    
    # Run synchronous tests
    tests = [
        ("Root Endpoint", client.test_root),
        ("Health Check", client.test_health),
        ("Research Endpoint", lambda: client.test_research("What are the benefits of FastAPI?")),
        ("Cache Stats", client.test_cache_stats),
        ("Error Handling", client.test_invalid_request),
        ("Cache Behavior", client.test_cache_behavior),
    ]
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Run async WebSocket test
    try:
        print("\nRunning WebSocket test...")
        success = asyncio.run(client.test_websocket())
        results.append(("WebSocket", success))
    except Exception as e:
        print(f"❌ WebSocket test failed with exception: {str(e)}")
        results.append(("WebSocket", False))
    
    # Print summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! API is ready for frontend integration.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    print("\n⚠️  Make sure the FastAPI server is running:")
    print("   cd backend")
    print("   python main.py")
    print("\nPress Enter to continue with tests...")
    input()
    
    run_all_tests()