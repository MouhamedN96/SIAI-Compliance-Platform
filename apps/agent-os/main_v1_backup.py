"""
SIAI Compliance Platform - Agent Backend
FastAPI server for document compliance analysis with AI agents
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
from datetime import datetime
import uuid

# Add packages to path
sys.path.append('/app/packages')

from memory.compliance_memory import ComplianceMemoryAgent
from agents.document_analyst import DocumentAnalystAgent

# Initialize FastAPI app
app = FastAPI(
    title="SIAI Compliance Platform API",
    description="AI-powered document compliance and risk analysis",
    version="1.0.0"
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

# Initialize LLM client
try:
    from openai import OpenAI
    llm_client = OpenAI(api_key=OPENAI_API_KEY)
except ImportError:
    print("WARNING: OpenAI library not installed. Install with: pip install openai")
    llm_client = None

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


# ============================================================================
# Pydantic Models
# ============================================================================

class DocumentAnalysisRequest(BaseModel):
    document_id: str
    document_text: str
    filename: str
    document_type: Optional[str] = "unknown"
    frameworks: Optional[List[str]] = None  # ['gdpr', 'soc2', 'contract_risk']
    metadata: Optional[Dict[str, Any]] = {}


class DocumentAnalysisResponse(BaseModel):
    document_id: str
    analysis_timestamp: str
    frameworks_analyzed: List[str]
    findings: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]]
    risk_score: int
    learned_patterns_applied: List[Dict[str, Any]]
    actions_taken: List[str]


class FindingFeedbackRequest(BaseModel):
    finding_id: str
    feedback: str  # 'accepted', 'rejected', 'false_positive'
    action_taken: Optional[str] = None


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
def root():
    return {
        "service": "SIAI Compliance Platform",
        "status": "running",
        "version": "1.0.0",
        "agent_ready": document_analyst is not None
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
        "llm_model": LLM_MODEL
    }


# ============================================================================
# Document Analysis Endpoints
# ============================================================================

@app.post("/api/documents/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(request: DocumentAnalysisRequest):
    """
    Analyze a document for compliance and risks.
    This triggers the full perceive-plan-act-reflect loop.
    """
    
    if not document_analyst:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check OPENAI_API_KEY.")
    
    try:
        # Prepare metadata
        metadata = {
            "filename": request.filename,
            "document_type": request.document_type,
            **request.metadata
        }
        
        # Run analysis
        results = document_analyst.analyze_document(
            document_id=request.document_id,
            document_text=request.document_text,
            document_metadata=metadata,
            frameworks=request.frameworks
        )
        
        return DocumentAnalysisResponse(**results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("unknown"),
    frameworks: Optional[str] = Form(None)
):
    """
    Upload a document and analyze it.
    """
    
    if not document_analyst:
        raise HTTPException(status_code=503, detail="Agent not initialized.")
    
    try:
        # Read file content
        content = await file.read()
        
        # For MVP, assume text files. In production, use PDF/DOCX parsers
        try:
            document_text = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Only text files supported in MVP. Use PDF/DOCX parser for production.")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Parse frameworks
        frameworks_list = frameworks.split(',') if frameworks else None
        
        # Prepare metadata
        metadata = {
            "filename": file.filename,
            "document_type": document_type,
            "file_size_bytes": len(content),
            "mime_type": file.content_type
        }
        
        # Run analysis
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
        raise HTTPException(status_code=500, detail=f"Upload and analysis failed: {str(e)}")


@app.get("/api/documents/{document_id}/findings")
async def get_document_findings(
    document_id: str,
    framework: Optional[str] = None,
    severity: Optional[str] = None
):
    """
    Retrieve findings for a specific document.
    """
    
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


@app.get("/api/documents/{document_id}/risk-profile")
async def get_document_risk_profile(document_id: str):
    """
    Get a complete risk profile for a document.
    """
    
    try:
        profile = memory_agent.get_document_risk_profile(document_id)
        return profile
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve risk profile: {str(e)}")


# ============================================================================
# Learning & Feedback Endpoints
# ============================================================================

@app.post("/api/findings/{finding_id}/feedback")
async def submit_finding_feedback(finding_id: str, request: FindingFeedbackRequest):
    """
    Submit feedback on a finding to help the agent learn.
    """
    
    try:
        memory_agent.learn_from_feedback(
            finding_id=finding_id,
            feedback=request.feedback,
            pattern_key=None  # In production, extract pattern_key from finding
        )
        
        return {
            "status": "feedback_recorded",
            "finding_id": finding_id,
            "feedback": request.feedback
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")


@app.get("/api/patterns")
async def get_learned_patterns(framework: Optional[str] = None):
    """
    Retrieve learned risk patterns (semantic memory).
    """
    
    try:
        patterns = memory_agent.get_reliable_patterns(framework=framework)
        
        return {
            "patterns": patterns,
            "count": len(patterns),
            "framework_filter": framework
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patterns: {str(e)}")


@app.get("/api/patterns/{pattern_key}")
async def get_pattern_detail(pattern_key: str):
    """
    Get details of a specific learned pattern.
    """
    
    try:
        pattern = memory_agent.semantic.get_pattern(pattern_key)
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        return pattern
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pattern: {str(e)}")


# ============================================================================
# Statistics & Monitoring
# ============================================================================

@app.get("/api/stats/overview")
async def get_platform_stats():
    """
    Get overall platform statistics.
    """
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Count documents
        cur.execute("SELECT COUNT(*) as count FROM documents WHERE is_archived = FALSE")
        doc_count = cur.fetchone()['count']
        
        # Count findings by severity
        cur.execute("""
            SELECT severity, COUNT(*) as count
            FROM compliance_findings
            GROUP BY severity
        """)
        findings_by_severity = {row['severity']: row['count'] for row in cur.fetchall()}
        
        # Count learned patterns
        cur.execute("SELECT COUNT(*) as count FROM risk_patterns WHERE precision_score >= 0.7")
        pattern_count = cur.fetchone()['count']
        
        # Top patterns
        cur.execute("""
            SELECT pattern_key, precision_score, frequency_observed, avg_severity
            FROM risk_patterns
            WHERE precision_score >= 0.7
            ORDER BY precision_score DESC, frequency_observed DESC
            LIMIT 5
        """)
        top_patterns = [dict(row) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return {
            "documents_analyzed": doc_count,
            "findings_by_severity": findings_by_severity,
            "learned_patterns": pattern_count,
            "top_patterns": top_patterns
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
