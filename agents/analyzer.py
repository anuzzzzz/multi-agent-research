# backend/agents/analyzer.py
"""
Analyzer Agent: Synthesizes and analyzes information from the Researcher
This agent uses GPT-4 to understand, evaluate, and extract insights
"""

from typing import Dict, List, Any
from openai import OpenAI
from datetime import datetime
import json

class AnalyzerAgent:
    """
    The Analyzer Agent takes search results and synthesizes them into insights.
    It's like having a data analyst who can quickly understand and summarize findings.
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the Analyzer with OpenAI client
        
        Args:
            openai_api_key: API key for OpenAI
            model: Which GPT model to use
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.name = "Analyzer Agent 🧠"
        
        # System prompt that defines how the analyzer should think
        self.system_prompt = """You are an expert research analyst. Your job is to:
1. Synthesize information from multiple sources
2. Identify key themes and patterns
3. Evaluate the credibility and relevance of sources
4. Extract the most important insights
5. Identify any gaps or contradictions in the information

Provide a structured analysis that will help create a comprehensive report.
Be critical and analytical, not just summarizing."""
    
    def analyze(self, search_results: str, original_query: str) -> Dict[str, Any]:
        """
        Analyze the search results and extract insights
        
        Args:
            search_results: Formatted results from the Researcher agent
            original_query: The original research question
            
        Returns:
            Dictionary containing analysis and insights
        """
        print(f"\n{self.name} starting analysis...")
        
        try:
            # Create the analysis prompt
            user_prompt = f"""
Research Question: {original_query}

Search Results to Analyze:
{search_results}

Please provide a comprehensive analysis including:
1. KEY FINDINGS: Main discoveries from the sources
2. PATTERNS: Common themes across sources
3. CREDIBILITY: Assessment of source reliability
4. INSIGHTS: Deeper insights beyond surface-level information
5. GAPS: What information is missing or unclear
6. SYNTHESIS: Overall synthesis connecting all findings
"""
            
            # Call GPT-4 for analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Some creativity but mostly factual
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            
            print(f"✅ {self.name} completed analysis")
            
            return {
                "status": "success",
                "original_query": original_query,
                "analysis": analysis,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(f"❌ {self.name} error: {error_msg}")
            
            return {
                "status": "error",
                "original_query": original_query,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
    
    def extract_key_points(self, analysis_results: Dict) -> List[str]:
        """
        Extract bullet points of key findings for the report
        
        Args:
            analysis_results: Results from the analyze method
            
        Returns:
            List of key points
        """
        if analysis_results["status"] == "error":
            return [f"Analysis failed: {analysis_results['error']}"]
        
        # Use GPT to extract key points in bullet form
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract 5-7 key bullet points from this analysis. Be concise."},
                    {"role": "user", "content": analysis_results["analysis"]}
                ],
                temperature=0.3,  # Low temperature for consistency
                max_tokens=300
            )
            
            # Split response into bullet points
            key_points = [
                point.strip().lstrip("•-*").strip() 
                for point in response.choices[0].message.content.split("\n") 
                if point.strip()
            ]
            
            return key_points
            
        except Exception as e:
            print(f"Failed to extract key points: {e}")
            return ["Error extracting key points"]
    
    def format_for_next_agent(self, analysis_results: Dict) -> str:
        """
        Format analysis for the Writer agent
        
        Args:
            analysis_results: Results from the analyze method
            
        Returns:
            Formatted string for the Writer agent
        """
        if analysis_results["status"] == "error":
            return f"Analysis failed: {analysis_results['error']}"
        
        formatted = f"RESEARCH QUESTION: {analysis_results['original_query']}\n\n"
        formatted += "ANALYSIS RESULTS:\n"
        formatted += "=" * 50 + "\n\n"
        formatted += analysis_results["analysis"]
        formatted += "\n\n" + "=" * 50
        formatted += f"\n\nAnalyzed by: {analysis_results['agent']}"
        formatted += f"\nTokens used: {analysis_results.get('tokens_used', 'N/A')}"
        
        return formatted


# Example usage and testing
if __name__ == "__main__":
    """
    Test the Analyzer Agent independently
    Run this file directly to test: python analyzer.py
    """
    import os
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.settings import settings
    
    # Create analyzer agent
    analyzer = AnalyzerAgent(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
    
    # Sample search results (simulating output from Researcher)
    sample_search_results = """
SEARCH QUERY: What are the latest advances in LangGraph for multi-agent systems?

SOURCES FOUND (3):

Source 1: Introduction to LangGraph
URL: https://langchain.com/docs/langgraph
Content: LangGraph is a library for building stateful, multi-actor applications with LLMs. 
It extends LangChain with the ability to create cyclical graphs and manage state...
Relevance Score: 0.95

Source 2: Multi-Agent Workflows in LangGraph
URL: https://blog.langchain.dev/multi-agent-workflows
Content: Recent advances include parallel agent execution, improved state management, 
and built-in human-in-the-loop capabilities...
Relevance Score: 0.92

Source 3: LangGraph Tutorial 2024
URL: https://www.youtube.com/watch?v=example
Content: This tutorial covers the latest features including checkpointing, time travel debugging,
and the new Studio visual editor for debugging agent workflows...
Relevance Score: 0.88
"""
    
    print("🧪 Testing Analyzer Agent")
    
    # Perform analysis
    results = analyzer.analyze(
        sample_search_results,
        "What are the latest advances in LangGraph for multi-agent systems?"
    )
    
    # Print results
    if results["status"] == "success":
        print("\n📊 Analysis Results:")
        print(results["analysis"][:1000])  # First 1000 chars
        
        print("\n🔑 Key Points:")
        key_points = analyzer.extract_key_points(results)
        for i, point in enumerate(key_points, 1):
            print(f"{i}. {point}")
    else:
        print(f"\n❌ Analysis failed: {results['error']}")