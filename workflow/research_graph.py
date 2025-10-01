# backend/workflow/research_graph.py
"""
LangGraph Orchestration: Coordinates the three agents in a stateful workflow
This is the brain that manages how agents work together
"""

from typing import Dict, TypedDict, Annotated, List, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from datetime import datetime
import json

# Import our agents
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.researcher import ResearcherAgent
from agents.analyzer import AnalyzerAgent
from agents.writer import WriterAgent
from config.settings import settings


# Define the state structure that will be passed between agents
class ResearchState(TypedDict):
    """
    The shared state that flows through all agents.
    Think of this as a notebook that each agent reads and writes to.
    """
    messages: Annotated[List[str], add_messages]  # Conversation history
    research_query: str  # What we're researching
    search_results: Dict  # Results from Researcher
    analysis: Dict  # Analysis from Analyzer
    final_report: Dict  # Report from Writer
    current_step: str  # Which step we're on
    error: str  # Any errors that occur


class ResearchWorkflow:
    """
    Orchestrates the multi-agent research workflow using LangGraph.
    This class manages how the three agents collaborate.
    """
    
    def __init__(self):
        """Initialize the workflow with all three agents"""
        print("🚀 Initializing Research Workflow...")
        
        # Initialize agents
        self.researcher = ResearcherAgent(settings.TAVILY_API_KEY)
        self.analyzer = AnalyzerAgent(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
        self.writer = WriterAgent(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
        
        # Build the workflow graph
        self.app = self._build_graph()
        print("✅ Workflow initialized successfully!")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow that connects all agents.
        This defines how data flows from one agent to another.
        """
        # Create the state graph
        workflow = StateGraph(ResearchState)
        
        # Add nodes (each node is an agent's action)
        workflow.add_node("research", self.research_node)
        workflow.add_node("analyze", self.analyze_node)
        workflow.add_node("write", self.write_node)
        
        # Define the flow (edges between nodes)
        workflow.set_entry_point("research")  # Start with research
        workflow.add_edge("research", "analyze")  # Then analyze
        workflow.add_edge("analyze", "write")  # Then write
        workflow.add_edge("write", END)  # Then finish
        
        # Compile the graph
        return workflow.compile()
    
    def research_node(self, state: ResearchState) -> ResearchState:
        """
        Research node: Uses the Researcher agent to search for information
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with search results
        """
        print("\n📍 Step 1: Research Node Activated")
        state["current_step"] = "research"
        
        try:
            # Get the research query
            query = state["research_query"]
            state["messages"].append(f"Researching: {query}")
            
            # Perform the search
            search_results = self.researcher.search(query, max_results=5)
            
            # Store results in state
            state["search_results"] = search_results
            
            if search_results["status"] == "success":
                state["messages"].append(
                    f"✅ Found {len(search_results['results']['sources'])} sources"
                )
            else:
                state["error"] = search_results.get("error", "Unknown error")
                state["messages"].append(f"❌ Research failed: {state['error']}")
            
        except Exception as e:
            state["error"] = str(e)
            state["messages"].append(f"❌ Research node error: {e}")
        
        return state
    
    def analyze_node(self, state: ResearchState) -> ResearchState:
        """
        Analysis node: Uses the Analyzer agent to synthesize findings
        
        Args:
            state: Current workflow state with search results
            
        Returns:
            Updated state with analysis
        """
        print("\n📍 Step 2: Analysis Node Activated")
        state["current_step"] = "analyze"
        
        try:
            # Check if we have search results
            if state.get("search_results", {}).get("status") != "success":
                state["error"] = "No search results to analyze"
                state["messages"].append("❌ Skipping analysis: No search results")
                return state
            
            # Format search results for analyzer
            formatted_results = self.researcher.format_for_next_agent(
                state["search_results"]
            )
            
            # Perform analysis
            analysis = self.analyzer.analyze(
                formatted_results,
                state["research_query"]
            )
            
            # Store analysis in state
            state["analysis"] = analysis
            
            if analysis["status"] == "success":
                state["messages"].append("✅ Analysis completed successfully")
            else:
                state["error"] = analysis.get("error", "Unknown error")
                state["messages"].append(f"❌ Analysis failed: {state['error']}")
            
        except Exception as e:
            state["error"] = str(e)
            state["messages"].append(f"❌ Analysis node error: {e}")
        
        return state
    
    def write_node(self, state: ResearchState) -> ResearchState:
        """
        Writing node: Uses the Writer agent to create the final report
        
        Args:
            state: Current workflow state with analysis
            
        Returns:
            Updated state with final report
        """
        print("\n📍 Step 3: Writing Node Activated")
        state["current_step"] = "write"
        
        try:
            # Check if we have analysis results
            if state.get("analysis", {}).get("status") != "success":
                state["error"] = "No analysis to write report from"
                state["messages"].append("❌ Skipping report: No analysis")
                return state
            
            # Format inputs for writer
            formatted_search = self.researcher.format_for_next_agent(
                state["search_results"]
            )
            formatted_analysis = self.analyzer.format_for_next_agent(
                state["analysis"]
            )
            
            # Generate report
            report = self.writer.write_report(
                query=state["research_query"],
                search_results=formatted_search,
                analysis=formatted_analysis,
                report_type="detailed"
            )
            
            # Store report in state
            state["final_report"] = report
            
            if report["status"] == "success":
                state["messages"].append(
                    f"✅ Report completed: {report['word_count']} words"
                )
            else:
                state["error"] = report.get("error", "Unknown error")
                state["messages"].append(f"❌ Report generation failed: {state['error']}")
            
        except Exception as e:
            state["error"] = str(e)
            state["messages"].append(f"❌ Writing node error: {e}")
        
        return state
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the complete research workflow
        
        Args:
            query: Research question to investigate
            
        Returns:
            Dictionary with the final report and metadata
        """
        print(f"\n{'='*60}")
        print(f"🔬 STARTING RESEARCH WORKFLOW")
        print(f"📝 Query: {query}")
        print(f"{'='*60}")
        
        # Initialize state
        initial_state = {
            "messages": [f"Starting research for: {query}"],
            "research_query": query,
            "search_results": {},
            "analysis": {},
            "final_report": {},
            "current_step": "initializing",
            "error": ""
        }
        
        try:
            # Run the workflow
            start_time = datetime.now()
            final_state = self.app.invoke(initial_state)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Prepare results
            if final_state.get("final_report", {}).get("status") == "success":
                print(f"\n✅ WORKFLOW COMPLETED SUCCESSFULLY in {duration:.1f} seconds")
                
                return {
                    "success": True,
                    "report": final_state["final_report"]["report"],
                    "metadata": {
                        "query": query,
                        "duration_seconds": duration,
                        "sources_found": len(
                            final_state.get("search_results", {})
                            .get("results", {})
                            .get("sources", [])
                        ),
                        "word_count": final_state["final_report"].get("word_count", 0),
                        "total_tokens": (
                            final_state.get("analysis", {}).get("tokens_used", 0) +
                            final_state.get("final_report", {}).get("tokens_used", 0)
                        ),
                        "workflow_steps": final_state["messages"]
                    }
                }
            else:
                print(f"\n❌ WORKFLOW FAILED: {final_state.get('error', 'Unknown error')}")
                
                return {
                    "success": False,
                    "error": final_state.get("error", "Workflow failed"),
                    "metadata": {
                        "query": query,
                        "duration_seconds": duration,
                        "failed_at_step": final_state.get("current_step", "unknown"),
                        "workflow_steps": final_state["messages"]
                    }
                }
                
        except Exception as e:
            print(f"\n❌ WORKFLOW EXCEPTION: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "query": query,
                    "error_type": type(e).__name__
                }
            }
    
    def run_with_streaming(self, query: str):
        """
        Run workflow with streaming updates (for real-time UI updates)
        Yields status updates as the workflow progresses
        """
        print(f"\n🔄 Starting streaming workflow for: {query}")
        
        # Initialize state
        initial_state = {
            "messages": [],
            "research_query": query,
            "search_results": {},
            "analysis": {},
            "final_report": {},
            "current_step": "initializing",
            "error": ""
        }
        
        # Stream updates as the workflow runs
        for output in self.app.stream(initial_state):
            # Yield status updates for each step
            for key, value in output.items():
                yield {
                    "step": key,
                    "status": "running",
                    "current_step": value.get("current_step", "unknown"),
                    "messages": value.get("messages", [])
                }
        
        # Yield final result
        yield {
            "step": "complete",
            "status": "finished",
            "report": output.get("final_report", {}).get("report", "")
        }


# Example usage and testing
if __name__ == "__main__":
    """
    Test the complete workflow
    Run this file directly to test: python research_graph.py
    """
    print("🧪 Testing Complete Research Workflow\n")
    
    # Create workflow
    workflow = ResearchWorkflow()
    
    # Test queries
    test_queries = [
        "What are the latest advances in LangGraph for building multi-agent systems?",
        # "How does RAG (Retrieval Augmented Generation) improve LLM performance?",
        # "What are the best practices for prompt engineering in 2024?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: {query}")
        print(f"{'='*60}")
        
        # Run the workflow
        result = workflow.run(query)
        
        if result["success"]:
            print("\n📄 FINAL REPORT:")
            print("="*60)
            print(result["report"][:1500])  # First 1500 chars
            print("="*60)
            
            print("\n📊 METADATA:")
            print(f"Duration: {result['metadata']['duration_seconds']:.1f} seconds")
            print(f"Sources: {result['metadata']['sources_found']}")
            print(f"Words: {result['metadata']['word_count']}")
            print(f"Tokens: {result['metadata']['total_tokens']}")
            
            # Save report to file
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, "w") as f:
                f.write(result["report"])
            print(f"\n💾 Report saved to: {filename}")
        else:
            print(f"\n❌ Workflow failed: {result['error']}")
            print(f"Failed at: {result['metadata'].get('failed_at_step', 'unknown')}")
            
        print("\n" + "="*60)