"""
Compliance Memory Module: Episodic and Semantic Memory for SIAI Agents
Adapted memory architecture for document compliance and risk analysis
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


class EpisodicComplianceMemory:
    """
    Stores specific compliance findings for documents.
    Each episode captures: document, finding, user feedback, resolution
    """
    
    def __init__(self, db_connection_string: str):
        self.conn_string = db_connection_string
    
    def store_finding(
        self,
        document_id: str,
        framework: str,
        finding_type: str,
        severity: str,
        title: str,
        description: str,
        location: Optional[str] = None,
        evidence: Optional[str] = None,
        recommendation: Optional[str] = None,
        agent_name: Optional[str] = None,
        agent_reasoning: Optional[str] = None
    ) -> str:
        """
        Store a compliance finding (episodic memory).
        
        Returns:
            finding_id: UUID of the stored finding
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO compliance_findings 
                (document_id, framework, finding_type, severity, title, description, 
                 location, evidence, recommendation, agent_name, agent_reasoning)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (document_id, framework, finding_type, severity, title, description,
                  location, evidence, recommendation, agent_name, agent_reasoning))
            
            finding_id = cur.fetchone()[0]
            conn.commit()
            
            return str(finding_id)
        
        finally:
            cur.close()
            conn.close()
    
    def get_document_findings(
        self,
        document_id: str,
        framework: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve findings for a specific document.
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            query = "SELECT * FROM compliance_findings WHERE document_id = %s"
            params = [document_id]
            
            if framework:
                query += " AND framework = %s"
                params.append(framework)
            
            if severity:
                query += " AND severity = %s"
                params.append(severity)
            
            query += " ORDER BY created_at DESC"
            
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
        
        finally:
            cur.close()
            conn.close()
    
    def record_user_feedback(
        self,
        finding_id: str,
        feedback: str,
        action_taken: Optional[str] = None
    ):
        """
        Record user feedback on a finding (for learning).
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE compliance_findings
                SET user_feedback = %s,
                    user_action_taken = %s,
                    resolved_at = CASE WHEN %s IN ('accepted', 'rejected') THEN NOW() ELSE resolved_at END
                WHERE id = %s
            """, (feedback, action_taken, feedback, finding_id))
            
            conn.commit()
        
        finally:
            cur.close()
            conn.close()


class SemanticComplianceMemory:
    """
    Stores generalized risk patterns learned across all documents.
    Learns which patterns are true positives vs false positives.
    """
    
    def __init__(self, db_connection_string: str):
        self.conn_string = db_connection_string
    
    def record_pattern_observation(
        self,
        pattern_key: str,
        framework: str,
        document_type: str,
        risk_indicator: str,
        is_true_positive: bool,
        severity: Optional[str] = None
    ):
        """
        Record an observation of a risk pattern.
        Updates precision score based on user feedback.
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        
        try:
            # Check if pattern exists
            cur.execute("""
                SELECT id, frequency_observed, true_positive_count, false_positive_count
                FROM risk_patterns
                WHERE pattern_key = %s
            """, (pattern_key,))
            
            result = cur.fetchone()
            
            if result:
                # Update existing pattern
                pattern_id, freq, tp_count, fp_count = result
                
                freq += 1
                if is_true_positive:
                    tp_count += 1
                else:
                    fp_count += 1
                
                total = tp_count + fp_count
                precision = tp_count / total if total > 0 else 0.0
                confidence = min(1.0, freq / 100.0)  # Confidence increases with observations
                
                cur.execute("""
                    UPDATE risk_patterns
                    SET frequency_observed = %s,
                        true_positive_count = %s,
                        false_positive_count = %s,
                        precision_score = %s,
                        confidence_score = %s,
                        observation_count = %s,
                        last_updated_at = NOW()
                    WHERE id = %s
                """, (freq, tp_count, fp_count, precision, confidence, freq, pattern_id))
            
            else:
                # Create new pattern
                tp_count = 1 if is_true_positive else 0
                fp_count = 0 if is_true_positive else 1
                freq = 1
                precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
                confidence = 0.01  # Low confidence with just 1 observation
                
                cur.execute("""
                    INSERT INTO risk_patterns
                    (pattern_key, pattern_description, framework, document_type, risk_indicator,
                     frequency_observed, true_positive_count, false_positive_count, 
                     precision_score, confidence_score, avg_severity, observation_count, learned_rule)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
                """, (
                    pattern_key,
                    f"Pattern: {risk_indicator} in {document_type}",
                    framework,
                    document_type,
                    risk_indicator,
                    freq,
                    tp_count,
                    fp_count,
                    precision,
                    confidence,
                    severity or 'medium',
                    f"Early pattern for {risk_indicator}"
                ))
            
            conn.commit()
        
        finally:
            cur.close()
            conn.close()
    
    def get_high_precision_patterns(
        self,
        framework: Optional[str] = None,
        min_precision: float = 0.7,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get patterns with high precision and confidence.
        These are reliable indicators of real risks.
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            query = """
                SELECT * FROM risk_patterns
                WHERE precision_score >= %s
                  AND confidence_score >= %s
            """
            params = [min_precision, min_confidence]
            
            if framework:
                query += " AND framework = %s"
                params.append(framework)
            
            query += " ORDER BY precision_score DESC, confidence_score DESC"
            
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
        
        finally:
            cur.close()
            conn.close()
    
    def get_pattern(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by key."""
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT * FROM risk_patterns
                WHERE pattern_key = %s
            """, (pattern_key,))
            
            result = cur.fetchone()
            return dict(result) if result else None
        
        finally:
            cur.close()
            conn.close()
    
    def get_remediation_template(self, pattern_key: str) -> Optional[str]:
        """Get the standard remediation for a pattern."""
        pattern = self.get_pattern(pattern_key)
        return pattern.get('remediation_template') if pattern else None


class ComplianceMemoryAgent:
    """
    Unified memory interface for compliance analysis.
    Combines episodic (findings) and semantic (patterns) memory.
    """
    
    def __init__(self, db_connection_string: str):
        self.episodic = EpisodicComplianceMemory(db_connection_string)
        self.semantic = SemanticComplianceMemory(db_connection_string)
    
    def remember_finding(
        self,
        document_id: str,
        framework: str,
        finding_type: str,
        severity: str,
        title: str,
        description: str,
        pattern_key: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Store a finding and update pattern learning.
        """
        # Store episodic memory (the specific finding)
        finding_id = self.episodic.store_finding(
            document_id=document_id,
            framework=framework,
            finding_type=finding_type,
            severity=severity,
            title=title,
            description=description,
            **kwargs
        )
        
        # If this finding matches a known pattern, record observation
        # (In production, this would be determined by the agent)
        if pattern_key:
            self.semantic.record_pattern_observation(
                pattern_key=pattern_key,
                framework=framework,
                document_type=kwargs.get('document_type', 'unknown'),
                risk_indicator=kwargs.get('evidence', ''),
                is_true_positive=True,  # Assume true until user feedback says otherwise
                severity=severity
            )
        
        return finding_id
    
    def learn_from_feedback(
        self,
        finding_id: str,
        feedback: str,
        pattern_key: Optional[str] = None
    ):
        """
        Learn from user feedback on a finding.
        Updates both episodic and semantic memory.
        """
        # Update episodic memory
        self.episodic.record_user_feedback(finding_id, feedback)
        
        # Update semantic memory (pattern learning)
        if pattern_key:
            is_true_positive = feedback in ['accepted', 'true_positive']
            # Would need to fetch finding details to update pattern
            # Simplified for MVP
    
    def get_reliable_patterns(
        self,
        framework: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get patterns that are reliable (high precision and confidence)."""
        return self.semantic.get_high_precision_patterns(
            framework=framework,
            min_precision=0.7,
            min_confidence=0.5
        )
    
    def get_document_risk_profile(self, document_id: str) -> Dict[str, Any]:
        """
        Get a complete risk profile for a document.
        """
        findings = self.episodic.get_document_findings(document_id)
        
        # Aggregate by severity
        profile = {
            "total_findings": len(findings),
            "critical": len([f for f in findings if f['severity'] == 'critical']),
            "high": len([f for f in findings if f['severity'] == 'high']),
            "medium": len([f for f in findings if f['severity'] == 'medium']),
            "low": len([f for f in findings if f['severity'] == 'low']),
            "frameworks_analyzed": list(set(f['framework'] for f in findings)),
            "findings": findings
        }
        
        return profile
