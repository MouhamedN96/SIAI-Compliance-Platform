"""
Document Analyst Agent
Main orchestrator for SIAI compliance analysis.
Implements the perceive -> plan -> act -> reflect loop for continuous learning.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .compliance_agents import GDPRComplianceAgent, SOC2ComplianceAgent, ContractRiskAgent, ComplianceFinding
from ..memory.compliance_memory import ComplianceMemoryAgent


@dataclass
class DocumentState:
    """Current state of a document being analyzed"""
    document_id: str
    document_data: Dict[str, Any]
    document_type: str
    text_content: str
    intent: str  # 'full_analysis', 'quick_scan', 're_analyze', 'validate_fix'


class DocumentAnalystAgent:
    """
    Main agent that orchestrates document compliance analysis.
    Implements continuous learning through the perceive-plan-act-reflect cycle.
    """
    
    def __init__(
        self,
        llm_client,
        memory: ComplianceMemoryAgent,
        model: str = "gpt-4o"
    ):
        """
        Args:
            llm_client: LiteLLM or OpenAI client
            memory: ComplianceMemoryAgent instance
            model: LLM model identifier
        """
        self.llm = llm_client
        self.memory = memory
        self.model = model
        self.name = "document_analyst"
        
        # Initialize specialized agents
        self.gdpr_agent = GDPRComplianceAgent(llm_client, model)
        self.soc2_agent = SOC2ComplianceAgent(llm_client, model)
        self.contract_agent = ContractRiskAgent(llm_client, model)
        
        self.current_plan = []
    
    def analyze_document(
        self,
        document_id: str,
        document_text: str,
        document_metadata: Dict[str, Any],
        frameworks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Analyze a document using the full agentic loop.
        
        Args:
            document_id: UUID of the document
            document_text: Full text content
            document_metadata: Metadata (filename, type, etc.)
            frameworks: Which frameworks to analyze (default: auto-detect)
        
        Returns:
            Complete analysis with findings, scores, and recommendations
        """
        
        # PERCEIVE: Understand the document
        state = self.perceive(document_id, document_text, document_metadata)
        
        # PLAN: Decide which analyses to run
        plan = self.plan(state, frameworks)
        
        # ACT: Execute the analysis plan
        results = self.act(plan, state)
        
        # REFLECT: Store findings and learn patterns
        self.reflect(state, plan, results)
        
        return results
    
    def perceive(
        self,
        document_id: str,
        document_text: str,
        document_metadata: Dict[str, Any]
    ) -> DocumentState:
        """
        PERCEIVE: Understand the document and determine what needs to be done.
        """
        
        document_type = document_metadata.get("document_type", "unknown")
        
        # Check if this document has been analyzed before
        previous_findings = self.memory.episodic.get_document_findings(document_id)
        
        # Determine intent based on context
        if previous_findings:
            intent = "re_analyze"  # Document has been analyzed before
        else:
            intent = "full_analysis"  # First time analyzing this document
        
        return DocumentState(
            document_id=document_id,
            document_data=document_metadata,
            document_type=document_type,
            text_content=document_text,
            intent=intent
        )
    
    def plan(
        self,
        state: DocumentState,
        requested_frameworks: Optional[List[str]] = None
    ) -> List[Tuple[str, Any]]:
        """
        PLAN: Decide which compliance frameworks to apply.
        Uses learned patterns to prioritize analyses.
        """
        
        plan = []
        
        # Determine which frameworks to apply
        if requested_frameworks:
            frameworks = requested_frameworks
        else:
            # Auto-detect based on document type
            frameworks = self._auto_detect_frameworks(state.document_type, state.text_content)
        
        # Add analyses to plan
        for framework in frameworks:
            if framework == "gdpr":
                plan.append(('run_gdpr_analysis', state))
            elif framework == "soc2":
                plan.append(('run_soc2_analysis', state))
            elif framework == "contract_risk":
                plan.append(('run_contract_analysis', state))
        
        # Always generate summary
        plan.append(('generate_summary', None))
        
        # Check learned patterns for this document type
        reliable_patterns = self.memory.get_reliable_patterns()
        if reliable_patterns:
            plan.append(('apply_learned_patterns', reliable_patterns))
        
        self.current_plan = plan
        return plan
    
    def act(self, plan: List[Tuple[str, Any]], state: DocumentState) -> Dict[str, Any]:
        """
        ACT: Execute the analysis plan.
        """
        
        results = {
            "document_id": state.document_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "frameworks_analyzed": [],
            "findings": [],
            "summary": None,
            "learned_patterns_applied": [],
            "actions_taken": []
        }
        
        all_findings: List[ComplianceFinding] = []
        
        for action_type, action_param in plan:
            
            if action_type == 'run_gdpr_analysis':
                # Run GDPR analysis
                findings = self.gdpr_agent.analyze_document(
                    state.text_content,
                    state.document_data
                )
                all_findings.extend(findings)
                results["frameworks_analyzed"].append("gdpr")
                results["actions_taken"].append("GDPR compliance analysis completed")
            
            elif action_type == 'run_soc2_analysis':
                # Run SOC 2 analysis
                findings = self.soc2_agent.analyze_document(
                    state.text_content,
                    state.document_data
                )
                all_findings.extend(findings)
                results["frameworks_analyzed"].append("soc2")
                results["actions_taken"].append("SOC 2 compliance analysis completed")
            
            elif action_type == 'run_contract_analysis':
                # Run contract risk analysis
                findings = self.contract_agent.analyze_document(
                    state.text_content,
                    state.document_data
                )
                all_findings.extend(findings)
                results["frameworks_analyzed"].append("contract_risk")
                results["actions_taken"].append("Contract risk analysis completed")
            
            elif action_type == 'generate_summary':
                # Generate executive summary
                summary = self._generate_summary(all_findings, state)
                results["summary"] = summary
                results["actions_taken"].append("Executive summary generated")
            
            elif action_type == 'apply_learned_patterns':
                # Apply learned patterns
                patterns = action_param
                results["learned_patterns_applied"] = [
                    {
                        "pattern_key": p.get("pattern_key"),
                        "precision": p.get("precision_score"),
                        "risk_indicator": p.get("risk_indicator"),
                        "remediation": p.get("remediation_template")
                    }
                    for p in patterns[:3]  # Top 3 patterns
                ]
                results["actions_taken"].append(f"Applied {len(patterns)} learned patterns")
        
        # Convert findings to dict format
        results["findings"] = [
            {
                "framework": f.framework,
                "finding_type": f.finding_type,
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "location": f.location,
                "evidence": f.evidence,
                "recommendation": f.recommendation,
                "reasoning": f.reasoning
            }
            for f in all_findings
        ]
        
        # Calculate risk score
        results["risk_score"] = self._calculate_risk_score(all_findings)
        
        return results
    
    def reflect(
        self,
        state: DocumentState,
        plan: List[Tuple[str, Any]],
        results: Dict[str, Any]
    ):
        """
        REFLECT: Store findings in memory and update pattern learning.
        This is where the agent learns.
        """
        
        # Store all findings in episodic memory
        for finding in results["findings"]:
            self.memory.remember_finding(
                document_id=state.document_id,
                framework=finding["framework"],
                finding_type=finding["finding_type"],
                severity=finding["severity"],
                title=finding["title"],
                description=finding["description"],
                location=finding.get("location"),
                evidence=finding.get("evidence"),
                recommendation=finding.get("recommendation"),
                agent_name=self.name,
                agent_reasoning=finding.get("reasoning"),
                document_type=state.document_type
            )
    
    def _auto_detect_frameworks(self, document_type: str, text_content: str) -> List[str]:
        """
        Auto-detect which compliance frameworks to apply based on document type and content.
        """
        frameworks = []
        
        # Document type heuristics
        if document_type in ['contract', 'agreement', 'terms']:
            frameworks.append('contract_risk')
        
        if document_type in ['policy', 'compliance_doc', 'procedure']:
            # Check content for keywords
            text_lower = text_content.lower()
            
            if any(keyword in text_lower for keyword in ['gdpr', 'personal data', 'data subject', 'data protection']):
                frameworks.append('gdpr')
            
            if any(keyword in text_lower for keyword in ['soc 2', 'soc2', 'security controls', 'trust service']):
                frameworks.append('soc2')
        
        # Default: if nothing detected, run contract analysis (safest default)
        if not frameworks:
            frameworks.append('contract_risk')
        
        return frameworks
    
    def _generate_summary(self, findings: List[ComplianceFinding], state: DocumentState) -> Dict[str, Any]:
        """Generate an executive summary of the analysis."""
        
        critical = [f for f in findings if f.severity == 'critical']
        high = [f for f in findings if f.severity == 'high']
        medium = [f for f in findings if f.severity == 'medium']
        low = [f for f in findings if f.severity == 'low']
        
        return {
            "document_name": state.document_data.get("filename", "Unknown"),
            "document_type": state.document_type,
            "total_findings": len(findings),
            "critical_issues": len(critical),
            "high_issues": len(high),
            "medium_issues": len(medium),
            "low_issues": len(low),
            "top_risks": [
                {
                    "title": f.title,
                    "severity": f.severity,
                    "recommendation": f.recommendation
                }
                for f in (critical + high)[:5]  # Top 5 most critical
            ],
            "overall_assessment": self._assess_overall_risk(len(critical), len(high), len(medium))
        }
    
    def _calculate_risk_score(self, findings: List[ComplianceFinding]) -> int:
        """
        Calculate an overall risk score (0-100, where 100 is highest risk).
        """
        if not findings:
            return 0
        
        # Weight by severity
        score = 0
        for f in findings:
            if f.severity == 'critical':
                score += 25
            elif f.severity == 'high':
                score += 15
            elif f.severity == 'medium':
                score += 5
            elif f.severity == 'low':
                score += 1
        
        # Cap at 100
        return min(100, score)
    
    def _assess_overall_risk(self, critical: int, high: int, medium: int) -> str:
        """Assess overall risk level."""
        if critical > 0:
            return "high_risk"
        elif high >= 3:
            return "high_risk"
        elif high > 0 or medium >= 5:
            return "moderate_risk"
        else:
            return "low_risk"
