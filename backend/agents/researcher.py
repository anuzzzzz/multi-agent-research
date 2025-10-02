# backend/agents/researcher.py
"""
Researcher Agent: Responsible for searching the web and gathering information
This agent uses Tavily API to find relevant, up-to-date information
"""

from typing import Dict, List, Any
from tavily import TavilyClient
from datetime import datetime
import json

class ResearcherAgent:
    """
    The Researcher Agent searches the web for information about a given topic.
    It's like having a research assistant who knows how to find the best sources.
    """
    
    def __init__(self, tavily_api_key: str):
        """
        Initialize the Researcher with Tavily client
        
        Args:
            tavily_api_key: API key for Tavily search service
        """
        self.client = TavilyClient(api_key=tavily_api_key)
        self.name = "Researcher Agent 🔍"
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search the web for information about the query
        
        Args:
            query: What to search for
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results and metadata
        """
        print(f"\n{self.name} starting search for: '{query}'")
        
        try:
            # Perform the search using Tavily
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=True,  # Get a quick answer if available
                include_raw_content=False,  # We don't need the full HTML
                include_images=False,  # Skip images for now
                search_depth="advanced"  # Use advanced search for better results
            )
            
            # Process and structure the results
            results = self._process_results(response)
            
            print(f"✅ {self.name} found {len(results['sources'])} relevant sources")
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            print(f"❌ {self.name} error: {error_msg}")
            
            return {
                "status": "error",
                "query": query,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
    
    def _process_results(self, response: Dict) -> Dict[str, Any]:
        """
        Process raw Tavily response into structured format
        
        Args:
            response: Raw response from Tavily API
            
        Returns:
            Structured search results
        """
        processed = {
            "answer": response.get("answer", ""),  # Quick answer if available
            "sources": [],
            "query_used": response.get("query", "")
        }
        
        # Process each search result
        for result in response.get("results", []):
            source = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0),  # Relevance score
                "published_date": result.get("published_date", "")
            }
            
            # Only include sources with actual content
            if source["content"] and source["title"]:
                processed["sources"].append(source)
        
        return processed
    
    def format_for_next_agent(self, search_results: Dict) -> str:
        """
        Format search results for the Analyzer agent
        
        Args:
            search_results: Results from the search method
            
        Returns:
            Formatted string for the next agent
        """
        if search_results["status"] == "error":
            return f"Search failed: {search_results['error']}"
        
        results = search_results["results"]
        formatted = f"SEARCH QUERY: {search_results['query']}\n\n"
        
        # Add quick answer if available
        if results.get("answer"):
            formatted += f"QUICK ANSWER:\n{results['answer']}\n\n"
        
        # Add sources
        formatted += f"SOURCES FOUND ({len(results['sources'])}):\n\n"
        
        for i, source in enumerate(results["sources"], 1):
            formatted += f"Source {i}: {source['title']}\n"
            formatted += f"URL: {source['url']}\n"
            formatted += f"Content: {source['content'][:500]}...\n"  # Truncate long content
            formatted += f"Relevance Score: {source['score']:.2f}\n"
            formatted += "-" * 50 + "\n"
        
        return formatted


# Example usage and testing
if __name__ == "__main__":
    """
    Test the Researcher Agent independently
    Run this file directly to test: python researcher.py
    """
    import os
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.settings import settings
    
    # Create researcher agent
    researcher = ResearcherAgent(settings.TAVILY_API_KEY)
    
    # Test search
    test_query = "What are the latest advances in LangGraph for multi-agent systems?"
    print(f"🧪 Testing Researcher Agent with query: '{test_query}'")
    
    # Perform search
    results = researcher.search(test_query, max_results=3)
    
    # Print results
    if results["status"] == "success":
        print("\n📊 Search Results:")
        print(json.dumps(results, indent=2, default=str)[:1000])  # Print first 1000 chars
        
        print("\n📝 Formatted for next agent:")
        formatted = researcher.format_for_next_agent(results)
        print(formatted[:800])  # Print first 800 chars
    else:
        print(f"\n❌ Search failed: {results['error']}")