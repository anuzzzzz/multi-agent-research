# backend/test_complete_system.py
"""
Test file to run the complete multi-agent research system
This tests Phase 2 (agents) and Phase 3 (orchestration) together
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from workflow.research_graph import ResearchWorkflow
from config.settings import settings
import json
from datetime import datetime


def test_individual_agents():
    """Test each agent individually first"""
    print("\n" + "="*60)
    print("🧪 TESTING INDIVIDUAL AGENTS")
    print("="*60)
    
    from agents.researcher import ResearcherAgent
    from agents.analyzer import AnalyzerAgent
    from agents.writer import WriterAgent
    
    # Test Researcher
    print("\n1️⃣ Testing Researcher Agent...")
    researcher = ResearcherAgent(settings.TAVILY_API_KEY)
    search_results = researcher.search("What is LangGraph?", max_results=2)
    
    if search_results["status"] == "success":
        print(f"   ✅ Researcher working - Found {len(search_results['results']['sources'])} sources")
    else:
        print(f"   ❌ Researcher failed: {search_results.get('error')}")
        return False
    
    # Test Analyzer
    print("\n2️⃣ Testing Analyzer Agent...")
    analyzer = AnalyzerAgent(settings.OPENAI_API_KEY)
    formatted_search = researcher.format_for_next_agent(search_results)
    analysis = analyzer.analyze(formatted_search, "What is LangGraph?")
    
    if analysis["status"] == "success":
        print(f"   ✅ Analyzer working - Used {analysis.get('tokens_used', 0)} tokens")
    else:
        print(f"   ❌ Analyzer failed: {analysis.get('error')}")
        return False
    
    # Test Writer
    print("\n3️⃣ Testing Writer Agent...")
    writer = WriterAgent(settings.OPENAI_API_KEY)
    formatted_analysis = analyzer.format_for_next_agent(analysis)
    report = writer.write_report(
        "What is LangGraph?",
        formatted_search,
        formatted_analysis,
        report_type="summary"
    )
    
    if report["status"] == "success":
        print(f"   ✅ Writer working - Generated {report.get('word_count', 0)} words")
    else:
        print(f"   ❌ Writer failed: {report.get('error')}")
        return False
    
    print("\n✅ All individual agents working correctly!")
    return True


def test_complete_workflow():
    """Test the complete workflow with multiple queries"""
    print("\n" + "="*60)
    print("🔬 TESTING COMPLETE WORKFLOW")
    print("="*60)
    
    # Create workflow
    workflow = ResearchWorkflow()
    
    # Test queries - from simple to complex
    test_queries = [
        {
            "query": "What are the key features of LangGraph?",
            "expected_time": 30,  # seconds
            "complexity": "simple"
        },
        {
            "query": "Compare LangGraph with other agent orchestration frameworks like AutoGen and CrewAI",
            "expected_time": 45,
            "complexity": "medium"
        },
        {
            "query": "What are the best practices for building production-ready multi-agent systems with LangGraph in 2024?",
            "expected_time": 60,
            "complexity": "complex"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_queries)}: {test['complexity'].upper()} QUERY")
        print(f"Query: {test['query']}")
        print(f"Expected time: <{test['expected_time']}s")
        print(f"{'='*60}")
        
        # Run workflow
        start = datetime.now()
        result = workflow.run(test["query"])
        duration = (datetime.now() - start).total_seconds()
        
        # Store result
        test_result = {
            "query": test["query"],
            "complexity": test["complexity"],
            "success": result["success"],
            "duration": duration,
            "expected_time": test["expected_time"],
            "within_time": duration <= test["expected_time"]
        }
        
        if result["success"]:
            test_result.update({
                "sources_found": result["metadata"]["sources_found"],
                "word_count": result["metadata"]["word_count"],
                "total_tokens": result["metadata"]["total_tokens"],
                "report_preview": result["report"][:200] + "..."
            })
            
            print(f"\n✅ SUCCESS in {duration:.1f}s")
            print(f"   Sources: {result['metadata']['sources_found']}")
            print(f"   Words: {result['metadata']['word_count']}")
            print(f"   Tokens: {result['metadata']['total_tokens']}")
            print(f"\n📄 Report Preview:")
            print(f"   {result['report'][:200]}...")
            
            # Save full report
            filename = f"test_report_{test['complexity']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, "w") as f:
                f.write(f"# Test Report: {test['complexity'].upper()}\n\n")
                f.write(f"**Query:** {test['query']}\n\n")
                f.write(f"**Generated in:** {duration:.1f} seconds\n\n")
                f.write("---\n\n")
                f.write(result["report"])
            print(f"\n💾 Full report saved to: {filename}")
            
        else:
            test_result["error"] = result.get("error", "Unknown error")
            print(f"\n❌ FAILED: {result.get('error')}")
        
        results.append(test_result)
    
    return results


def generate_test_report(results):
    """Generate a summary test report"""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY REPORT")
    print("="*60)
    
    total_tests = len(results)
    successful = sum(1 for r in results if r["success"])
    
    print(f"\n✅ Successful: {successful}/{total_tests}")
    print(f"❌ Failed: {total_tests - successful}/{total_tests}")
    print(f"📈 Success Rate: {(successful/total_tests)*100:.1f}%")
    
    print("\n📋 Detailed Results:")
    print("-"*60)
    
    for i, result in enumerate(results, 1):
        print(f"\nTest {i}: {result['complexity'].upper()}")
        print(f"   Query: {result['query'][:50]}...")
        print(f"   Status: {'✅ PASS' if result['success'] else '❌ FAIL'}")
        print(f"   Duration: {result['duration']:.1f}s (expected <{result['expected_time']}s)")
        
        if result["success"]:
            print(f"   Sources: {result['sources_found']}")
            print(f"   Words: {result['word_count']}")
            print(f"   Tokens: {result['total_tokens']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
    
    # Performance metrics
    if successful > 0:
        avg_duration = sum(r["duration"] for r in results if r["success"]) / successful
        avg_tokens = sum(r.get("total_tokens", 0) for r in results if r["success"]) / successful
        avg_words = sum(r.get("word_count", 0) for r in results if r["success"]) / successful
        
        print("\n📈 Performance Metrics:")
        print("-"*60)
        print(f"   Average Duration: {avg_duration:.1f} seconds")
        print(f"   Average Tokens: {avg_tokens:.0f}")
        print(f"   Average Words: {avg_words:.0f}")
        
        # Estimate costs
        token_cost = (avg_tokens / 1_000_000) * 0.15  # $0.15 per 1M tokens for GPT-4o-mini
        print(f"\n💰 Estimated Costs:")
        print(f"   Per Query: ~${token_cost:.4f}")
        print(f"   Per 100 Queries: ~${token_cost * 100:.2f}")
        print(f"   Per 1000 Queries: ~${token_cost * 1000:.2f}")
    
    print("\n" + "="*60)
    
    # Save test report
    report_filename = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Test summary saved to: {report_filename}")
    
    return all(r["success"] for r in results)


def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("    MULTI-AGENT RESEARCH ASSISTANT - COMPLETE SYSTEM TEST")
    print("🚀"*30)
    
    # Validate settings first
    if not settings.validate():
        print("\n❌ Please configure your API keys in .env file")
        return False
    
    # Test individual agents
    print("\n[Phase 1/2] Testing Individual Agents...")
    if not test_individual_agents():
        print("\n❌ Individual agent tests failed. Please debug agents first.")
        return False
    
    # Test complete workflow
    print("\n[Phase 2/2] Testing Complete Workflow...")
    results = test_complete_workflow()
    
    # Generate summary
    all_passed = generate_test_report(results)
    
    if all_passed:
        print("\n" + "🎉"*20)
        print("    ALL TESTS PASSED! System is working perfectly!")
        print("    Ready to move to Phase 4 (FastAPI Backend)")
        print("🎉"*20)
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)