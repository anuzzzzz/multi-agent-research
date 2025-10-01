# backend/agents/writer.py
"""
Writer Agent: Creates professional research reports from analyzed data
This agent uses GPT-4 to generate well-structured, readable reports
"""

from typing import Dict, Any, Optional
from openai import OpenAI
from datetime import datetime
import json

class WriterAgent:
    """
    The Writer Agent creates professional reports from research and analysis.
    It's like having a technical writer who can create clear, structured documents.
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the Writer with OpenAI client
        
        Args:
            openai_api_key: API key for OpenAI
            model: Which GPT model to use
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.name = "Writer Agent ✍️"
        
        # System prompt for report writing
        self.system_prompt = """You are a professional technical writer creating research reports.
Your reports should be:
1. Well-structured with clear sections
2. Professional but accessible
3. Comprehensive yet concise
4. Properly formatted in Markdown
5. Include an executive summary
6. Cite sources when referencing specific information

Use markdown formatting including:
- Headers (##, ###)
- Bullet points
- Bold for emphasis
- Numbered lists when appropriate
- Block quotes for important insights"""
    
    def write_report(self, 
                    query: str, 
                    search_results: str, 
                    analysis: str,
                    report_type: str = "detailed") -> Dict[str, Any]:
        """
        Generate a research report from search results and analysis
        
        Args:
            query: Original research question
            search_results: Formatted results from Researcher
            analysis: Analysis from Analyzer agent
            report_type: "detailed", "summary", or "executive"
            
        Returns:
            Dictionary containing the report and metadata
        """
        print(f"\n{self.name} generating {report_type} report...")
        
        try:
            # Create the report generation prompt
            user_prompt = self._create_report_prompt(
                query, search_results, analysis, report_type
            )
            
            # Generate the report
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            report = response.choices[0].message.content
            
            print(f"✅ {self.name} completed report generation")
            
            return {
                "status": "success",
                "query": query,
                "report": report,
                "report_type": report_type,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name,
                "tokens_used": response.usage.total_tokens,
                "word_count": len(report.split())
            }
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            print(f"❌ {self.name} error: {error_msg}")
            
            return {
                "status": "error",
                "query": query,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
    
    def _create_report_prompt(self, 
                             query: str, 
                             search_results: str, 
                             analysis: str,
                             report_type: str) -> str:
        """
        Create the appropriate prompt based on report type
        
        Args:
            query: Original research question
            search_results: Formatted results from Researcher
            analysis: Analysis from Analyzer agent
            report_type: Type of report to generate
            
        Returns:
            Formatted prompt for GPT-4
        """
        base_prompt = f"""
Research Question: {query}

Search Results:
{search_results[:1500]}  # Truncate if too long

Analysis:
{analysis}

"""
        
        if report_type == "detailed":
            base_prompt += """
Please create a DETAILED research report with the following sections:

# Research Report: [Title based on query]

## Executive Summary
[2-3 paragraph overview of key findings]

## Introduction
[Context and importance of the research question]

## Methodology
[Brief description of search and analysis approach]

## Key Findings
[Detailed findings with subsections as needed]

## Analysis & Insights
[Deeper analysis of the findings]

## Implications
[What these findings mean]

## Recommendations
[Actionable recommendations based on findings]

## Conclusion
[Summary and final thoughts]

## Sources
[List key sources used]
"""
        
        elif report_type == "summary":
            base_prompt += """
Please create a SUMMARY report (1 page) with:

# [Title]
## Quick Summary
## Key Findings (bullet points)
## Main Insights
## Recommendations
## Sources
"""
        
        else:  # executive
            base_prompt += """
Please create an EXECUTIVE BRIEF (very concise) with:

# Executive Brief: [Title]
## The Bottom Line (1 paragraph)
## Three Key Points
## Recommended Action
"""
        
        return base_prompt
    
    def generate_title(self, query: str) -> str:
        """
        Generate a professional title for the report
        
        Args:
            query: Research question
            
        Returns:
            Professional title
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Generate a concise, professional title for a research report. Maximum 10 words."},
                    {"role": "user", "content": f"Research question: {query}"}
                ],
                temperature=0.5,
                max_tokens=20
            )
            return response.choices[0].message.content.strip()
        except:
            return f"Research Report: {query[:50]}"
    
    def export_report(self, report_results: Dict, format: str = "markdown") -> str:
        """
        Export the report in different formats
        
        Args:
            report_results: Results from write_report method
            format: "markdown", "html", or "text"
            
        Returns:
            Formatted report string
        """
        if report_results["status"] == "error":
            return f"Error: {report_results['error']}"
        
        report = report_results["report"]
        
        if format == "markdown":
            return report
        
        elif format == "html":
            # Simple markdown to HTML conversion
            html = report.replace("# ", "<h1>").replace("</h1>\n", "</h1>")
            html = html.replace("## ", "<h2>").replace("</h2>\n", "</h2>")
            html = html.replace("### ", "<h3>").replace("</h3>\n", "</h3>")
            html = html.replace("**", "<strong>").replace("</strong>", "</strong>")
            html = html.replace("\n", "<br>\n")
            return f"<html><body>{html}</body></html>"
        
        else:  # text
            # Remove markdown formatting
            text = report.replace("#", "").replace("*", "")
            return text


# Example usage and testing
if __name__ == "__main__":
    """
    Test the Writer Agent independently
    Run this file directly to test: python writer.py
    """
    import os
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.settings import settings
    
    # Create writer agent
    writer = WriterAgent(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
    
    # Sample inputs (simulating outputs from previous agents)
    sample_query = "What are the latest advances in LangGraph for multi-agent systems?"
    
    sample_search_results = """
SOURCES FOUND (3):
Source 1: Introduction to LangGraph
Content: LangGraph is a library for building stateful, multi-actor applications...
Source 2: Multi-Agent Workflows
Content: Recent advances include parallel execution and state management...
"""
    
    sample_analysis = """
KEY FINDINGS: LangGraph has introduced several groundbreaking features:
1. Stateful graph management for complex workflows
2. Built-in checkpointing and time-travel debugging
3. Visual Studio for agent development
4. Human-in-the-loop capabilities

PATTERNS: Consistent focus on developer experience and debugging tools.
INSIGHTS: The platform is evolving from simple chains to complex orchestration.
"""
    
    print("🧪 Testing Writer Agent")
    
    # Generate different report types
    for report_type in ["summary", "detailed"]:
        print(f"\n📝 Generating {report_type} report...")
        
        results = writer.write_report(
            sample_query,
            sample_search_results,
            sample_analysis,
            report_type=report_type
        )
        
        if results["status"] == "success":
            print(f"\n✅ {report_type.upper()} REPORT:")
            print("=" * 50)
            print(results["report"][:800])  # First 800 chars
            print("=" * 50)
            print(f"📊 Stats: {results['word_count']} words, {results['tokens_used']} tokens")
        else:
            print(f"❌ Failed: {results['error']}")