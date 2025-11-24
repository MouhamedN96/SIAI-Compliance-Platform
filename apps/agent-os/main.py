"""
SIAI Compliance Platform - Agent Backend v2
FastAPI server with Composio integration and WebSocket support
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
from datetime import datetime
import uuid
import json
import asyncio

# Add packages to path
sys.path.append('/app/packages')

from memory.compliance_memory import ComplianceMemoryAgent
from agents.document_analyst import DocumentAnalystAgent

# Initialize FastAPI app
app = FastAPI(
    title="SIAI Compliance Platform API",
    description="AI-powered document compliance and risk analysis with Composio",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://siai_user:changeme123@localhost:5432/siai_compliance")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")

# Initialize LLM client
try:
    from openai import OpenAI
    llm_client = OpenAI(api_key=OPENAI_API_KEY)
except ImportError:
    print("WARNING: OpenAI library not installed")
    llm_client = None

# Initialize Composio
try:
    from composio import Composio
    composio_client = Composio(api_key=COMPOSIO_API_KEY) if COMPOSIO_API_KEY else None
except ImportError:
    print("WARNING: Composio library not installed. Install with: pip install composio")
    composio_client = None

# Initialize memory and agent
memory_agent = ComplianceMemoryAgent(DATABASE_URL)

if llm_client:
    document_analyst = DocumentAnalystAgent(
        llm_client=llm_client,
        memory=memory_agent,
        model=LLM_MODEL
    )
else:
    document_analyst = None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


# ============================================================================
# Pydantic Models
# ============================================================================

class DocumentAnalysisRequest(BaseModel):
    document_id: str
    document_text: str
    filename: str
    document_type: Optional[str] = "unknown"
    frameworks: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None  # For WebSocket updates


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    document_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}


class ComposioActionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    user_id: str = "default"


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket connection for real-time agent updates.
    """
    await manager.connect(session_id, websocket)
    
    try:
        await manager.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for ping/pong
            if data == "ping":
                await manager.send_message(session_id, {"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"WebSocket disconnected: {session_id}")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
def root():
    return {
        "service": "SIAI Compliance Platform v2",
        "status": "running",
        "version": "2.0.0",
        "agent_ready": document_analyst is not None,
        "composio_enabled": composio_client is not None
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    
    # Check database connection
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "agent": "ready" if document_analyst else "not initialized",
        "llm_model": LLM_MODEL,
        "composio": "enabled" if composio_client else "disabled"
    }


# ============================================================================
# Document Analysis with WebSocket Updates
# ============================================================================

@app.post("/api/documents/analyze-stream")
async def analyze_document_stream(request: DocumentAnalysisRequest):
    """
    Analyze a document with real-time WebSocket updates.
    """
    
    if not document_analyst:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Send start message
        await manager.send_message(session_id, {
            "type": "analysis_started",
            "document_id": request.document_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Perceive phase
        await manager.send_message(session_id, {
            "type": "agent_status",
            "phase": "perceive",
            "message": "Understanding document context..."
        })
        
        # Prepare metadata
        metadata = {
            "filename": request.filename,
            "document_type": request.document_type,
            **request.metadata
        }
        
        # Plan phase
        await manager.send_message(session_id, {
            "type": "agent_status",
            "phase": "plan",
            "message": "Planning compliance analysis..."
        })
        
        # Act phase
        await manager.send_message(session_id, {
            "type": "agent_status",
            "phase": "act",
            "message": "Analyzing document for compliance issues..."
        })
        
        # Run analysis
        results = document_analyst.analyze_document(
            document_id=request.document_id,
            document_text=request.document_text,
            document_metadata=metadata,
            frameworks=request.frameworks
        )
        
        # Reflect phase
        await manager.send_message(session_id, {
            "type": "agent_status",
            "phase": "reflect",
            "message": "Learning from analysis results..."
        })
        
        # Send findings incrementally
        for finding in results.get("findings", []):
            await manager.send_message(session_id, {
                "type": "finding_discovered",
                "finding": finding
            })
            await asyncio.sleep(0.1)  # Small delay for UX
        
        # Send completion
        await manager.send_message(session_id, {
            "type": "analysis_complete",
            "document_id": request.document_id,
            "summary": results.get("summary"),
            "risk_score": results.get("risk_score"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "session_id": session_id,
            "status": "analysis_started",
            "message": "Connect to WebSocket for real-time updates"
        }
    
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "error",
            "message": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================================================
# Chat with Agent
# ============================================================================

@app.post("/api/chat")
async def chat_with_agent(request: ChatMessageRequest):
    """
    Chat with the compliance agent about documents.
    """
    
    if not document_analyst:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Send thinking status
        await manager.send_message(request.session_id, {
            "type": "agent_thinking",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Get response from LLM
        messages = [
            {"role": "system", "content": "You are a compliance expert assistant. Help users understand compliance findings and provide actionable remediation advice."},
            {"role": "user", "content": request.message}
        ]
        
        if request.document_id:
            # Add document context
            findings = memory_agent.episodic.get_document_findings(request.document_id)
            context_msg = f"Document context: {len(findings)} findings found."
            messages.insert(1, {"role": "system", "content": context_msg})
        
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        
        # Send response via WebSocket
        await manager.send_message(request.session_id, {
            "type": "agent_response",
            "message": assistant_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "response": assistant_message,
            "session_id": request.session_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ============================================================================
# Composio Integration
# ============================================================================

@app.get("/api/composio/tools")
async def get_composio_tools(user_id: str = "default"):
    """
    Get available Composio tools for the user.
    """
    
    if not composio_client:
        raise HTTPException(status_code=503, detail="Composio not enabled")
    
    try:
        tools = composio_client.tools.get(
            user_id=user_id,
            toolkits=["SLACK", "GMAIL", "NOTION", "JIRA", "GITHUB"]
        )
        
        return {
            "user_id": user_id,
            "tools": [{"name": tool.name, "description": tool.description} for tool in tools],
            "count": len(tools)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")


@app.post("/api/composio/execute")
async def execute_composio_action(request: ComposioActionRequest):
    """
    Execute a Composio tool action.
    Example: Send compliance summary to Slack, create Jira ticket, etc.
    """
    
    if not composio_client:
        raise HTTPException(status_code=503, detail="Composio not enabled")
    
    try:
        # Execute the tool
        result = composio_client.tools.execute(
            tool_name=request.tool_name,
            user_id=request.user_id,
            parameters=request.parameters
        )
        
        return {
            "status": "success",
            "tool_name": request.tool_name,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


# ============================================================================
# Original Endpoints (kept for backwards compatibility)
# ============================================================================

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("unknown"),
    frameworks: Optional[str] = Form(None)
):
    """Upload and analyze document"""
    
    if not document_analyst:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        content = await file.read()
        
        try:
            document_text = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Only text files supported in MVP")
        
        document_id = str(uuid.uuid4())
        frameworks_list = frameworks.split(',') if frameworks else None
        
        metadata = {
            "filename": file.filename,
            "document_type": document_type,
            "file_size_bytes": len(content),
            "mime_type": file.content_type
        }
        
        results = document_analyst.analyze_document(
            document_id=document_id,
            document_text=document_text,
            document_metadata=metadata,
            frameworks=frameworks_list
        )
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "analysis": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/documents/{document_id}/findings")
async def get_document_findings(
    document_id: str,
    framework: Optional[str] = None,
    severity: Optional[str] = None
):
    """Retrieve findings for a document"""
    
    try:
        findings = memory_agent.episodic.get_document_findings(
            document_id=document_id,
            framework=framework,
            severity=severity
        )
        
        return {
            "document_id": document_id,
            "findings": findings,
            "count": len(findings)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve findings: {str(e)}")


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
