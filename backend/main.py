# backend/main.py
"""
FastAPI server for Multi-Agent Research Assistant
This serves as the API layer between the frontend and our agent system
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import json
import hashlib
import logging
import concurrent.futures

# Import our workflow and settings
from workflow.research_graph import ResearchWorkflow
from config.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Initialize FastAPI app
# ============================================
app = FastAPI(
    title="Multi-Agent Research Assistant API",
    description="API for AI-powered research using multiple specialized agents",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc"  # ReDoc at http://localhost:8000/redoc
)

# ============================================
# CORS Configuration
# ============================================
# This allows our Next.js frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vue/Vite dev server
        "http://127.0.0.1:5173",
        # Add your production domain here later
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================
# In-Memory Cache Implementation
# ============================================
class CacheManager:
    """
    Simple in-memory cache to avoid repeated API calls
    In production, you might want to use Redis instead
    """
    def __init__(self, ttl_hours: int = 24):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_hours = ttl_hours
        self.hits = 0
        self.misses = 0
    
    def _get_key(self, query: str) -> str:
        """Generate a unique cache key for the query"""
        # Create hash of lowercase, stripped query for consistency
        normalized_query = query.lower().strip()
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if available and not expired"""
        key = self._get_key(query)
        
        if key in self.cache:
            cached_item = self.cache[key]
            # Check if cache is still valid (within TTL)
            cache_age_hours = (datetime.now() - cached_item["timestamp"]).seconds / 3600
            
            if cache_age_hours < self.ttl_hours:
                self.hits += 1
                logger.info(f"Cache HIT for query: {query[:50]}...")
                return cached_item["data"]
            else:
                # Cache expired, remove it
                del self.cache[key]
                logger.info(f"Cache EXPIRED for query: {query[:50]}...")
        
        self.misses += 1
        logger.info(f"Cache MISS for query: {query[:50]}...")
        return None
    
    def set(self, query: str, data: Dict[str, Any]) -> None:
        """Store result in cache"""
        key = self._get_key(query)
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now(),
            "query": query
        }
        logger.info(f"Cached result for query: {query[:50]}...")
    
    def clear(self) -> None:
        """Clear all cached items"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_hours": self.ttl_hours
        }

# Initialize cache
cache = CacheManager(ttl_hours=24)

# Initialize workflow (single instance for reuse)
workflow = ResearchWorkflow()

# ============================================
# Pydantic Models for Request/Response
# ============================================
class ResearchRequest(BaseModel):
    """Model for research request"""
    query: str = Field(
        ...,  # Required field
        min_length=5,
        max_length=500,
        description="The research question or topic"
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached results if available"
    )
    report_type: str = Field(
        default="detailed",
        description="Type of report: 'detailed', 'summary', or 'executive'"
    )

class ResearchResponse(BaseModel):
    """Model for research response"""
    success: bool
    query: str
    report: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any]
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str
    timestamp: datetime
    cache_stats: Dict[str, Any]
    workflow_ready: bool
    apis_configured: Dict[str, bool]

# ============================================
# WebSocket Connection Manager
# ============================================
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_json(self, websocket: WebSocket, data: dict):
        """Send JSON data to specific client"""
        await websocket.send_json(data)
    
    async def broadcast(self, data: dict):
        """Broadcast to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                # Connection might be closed
                pass

# Initialize connection manager
manager = ConnectionManager()

# ============================================
# API Endpoints
# ============================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Multi-Agent Research Assistant API",
        "version": "1.0.0",
        "description": "AI-powered research using specialized agents",
        "endpoints": {
            "docs": "http://localhost:8000/docs",
            "health": "http://localhost:8000/health",
            "research": "POST http://localhost:8000/api/research",
            "websocket": "ws://localhost:8000/ws"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """
    Health check endpoint
    Returns system status and configuration
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        cache_stats=cache.stats(),
        workflow_ready=workflow is not None,
        apis_configured={
            "openai": bool(settings.OPENAI_API_KEY),
            "tavily": bool(settings.TAVILY_API_KEY)
        }
    )

@app.post("/api/research", response_model=ResearchResponse, tags=["Research"])
async def research_endpoint(request: ResearchRequest):
    """
    Main research endpoint
    Processes research queries using the multi-agent workflow
    
    Args:
        request: ResearchRequest containing the query and options
    
    Returns:
        ResearchResponse with the generated report or error
    """
    logger.info(f"Research request received: {request.query}")
    
    try:
        # Check cache first (if enabled)
        if request.use_cache:
            cached_result = cache.get(request.query)
            if cached_result:
                return ResearchResponse(
                    success=True,
                    query=request.query,
                    report=cached_result.get("report"),
                    metadata=cached_result.get("metadata", {}),
                    cached=True
                )
        
        # Run the research workflow
        logger.info(f"Running workflow for: {request.query}")
        result = workflow.run(request.query)
        
        if result["success"]:
            # Cache the successful result
            cache.set(request.query, result)
            
            return ResearchResponse(
                success=True,
                query=request.query,
                report=result["report"],
                metadata=result["metadata"],
                cached=False
            )
        else:
            # Workflow failed
            return ResearchResponse(
                success=False,
                query=request.query,
                error=result.get("error", "Unknown error occurred"),
                metadata=result.get("metadata", {}),
                cached=False
            )
    
    except Exception as e:
        logger.error(f"Error processing research request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.delete("/api/cache", tags=["Cache"])
async def clear_cache():
    """Clear the entire cache"""
    cache.clear()
    return {"message": "Cache cleared successfully", "stats": cache.stats()}

@app.get("/api/cache/stats", tags=["Cache"])
async def cache_stats():
    """Get cache statistics"""
    return cache.stats()

# ============================================
# WebSocket Endpoint for Real-time Updates
# ============================================

async def run_workflow_with_updates(query: str, websocket: WebSocket, manager):
    """
    Run the research workflow with real-time progress updates
    """
    try:
        # Send initial research progress
        await manager.send_json(websocket, {
            "type": "progress",
            "step": "research",
            "message": "🔍 Searching for information...",
            "progress": 10
        })

        # Run the workflow in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start the workflow
            future = loop.run_in_executor(executor, workflow.run, query)

            # Send progress updates while waiting
            progress_steps = [
                (5, "research", "🔍 Connecting to search services..."),
                (10, "research", "🔍 Searching for information..."),
                (15, "research", "🔍 Gathering sources..."),
                (20, "research", "🔍 Processing search results..."),
                (30, "analyze", "🧠 Starting analysis..."),
                (40, "analyze", "🧠 Analyzing findings..."),
                (50, "analyze", "🧠 Synthesizing information..."),
                (60, "analyze", "🧠 Extracting insights..."),
                (70, "write", "✍️ Starting report generation..."),
                (80, "write", "✍️ Writing report sections..."),
                (90, "write", "✍️ Formatting final report..."),
            ]

            for seconds, step, message in progress_steps:
                if future.done():
                    break

                await manager.send_json(websocket, {
                    "type": "progress",
                    "step": step,
                    "message": message,
                    "progress": (seconds / 45) * 100  # Estimate based on ~45 second total time
                })

                # Wait a bit before next update
                await asyncio.sleep(3)

                # Check if done
                if future.done():
                    break

            # Get the result (with timeout)
            try:
                result = await asyncio.wait_for(
                    asyncio.wrap_future(future),
                    timeout=60  # 60 second timeout
                )

                if result["success"]:
                    # Cache the result
                    cache.set(query, result)

                    # Send complete message
                    await manager.send_json(websocket, {
                        "type": "complete",
                        "cached": False,
                        "report": result["report"],
                        "metadata": result["metadata"]
                    })
                else:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "error": result.get("error", "Research failed")
                    })

            except asyncio.TimeoutError:
                await manager.send_json(websocket, {
                    "type": "error",
                    "error": "Research timeout - the process took too long"
                })
            except Exception as e:
                await manager.send_json(websocket, {
                    "type": "error",
                    "error": str(e)
                })

    except Exception as e:
        logger.error(f"Workflow error: {str(e)}")
        await manager.send_json(websocket, {
            "type": "error",
            "error": f"Workflow error: {str(e)}"
        })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time research updates
    Allows frontend to receive progress updates as agents work
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_json()
            query = data.get("query", "")
            
            if not query:
                await manager.send_json(websocket, {
                    "type": "error",
                    "error": "No query provided"
                })
                continue
            
            logger.info(f"WebSocket research request: {query}")
            
            # Send initial acknowledgment
            await manager.send_json(websocket, {
                "type": "status",
                "message": "Research started",
                "step": "initializing",
                "timestamp": datetime.now().isoformat()
            })
            
            # Check cache first
            cached_result = cache.get(query)
            if cached_result:
                await manager.send_json(websocket, {
                    "type": "complete",
                    "cached": True,
                    "report": cached_result.get("report"),
                    "metadata": cached_result.get("metadata", {})
                })
                continue
            
            try:
                # Run workflow asynchronously with progress updates
                await run_workflow_with_updates(query, websocket, manager)

            except Exception as e:
                logger.error(f"Error during research: {str(e)}")
                await manager.send_json(websocket, {
                    "type": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await manager.send_json(websocket, {
                "type": "error",
                "error": str(e)
            })
        except:
            pass
        manager.disconnect(websocket)

# ============================================
# Startup and Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    logger.info("🚀 Starting Multi-Agent Research Assistant API...")
    
    # Validate configuration
    if not settings.validate():
        logger.error("❌ Invalid configuration. Please check your .env file")
        raise RuntimeError("Invalid configuration")
    
    logger.info("✅ API started successfully")
    logger.info(f"📚 Documentation available at: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown"""
    logger.info("Shutting down API...")
    # Save cache stats before shutdown
    logger.info(f"Final cache stats: {cache.stats()}")

# ============================================
# Run the server
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )