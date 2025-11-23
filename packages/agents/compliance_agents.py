"""
Compliance Framework Agents
Specialized agents for GDPR, SOC2, and Contract Risk analysis
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class ComplianceFinding:
    """Structured compliance finding"""
    framework: str
    finding_type: str  # 'violation', 'gap', 'risk', 'compliant'
    severity: str  # 'critical', 'high', 'medium', 'low'
    title: str
    description: str
    location: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    reasoning: Optional[str] = None


class GDPRComplianceAgent:
    """
    Agent specialized in GDPR (General Data Protection Regulation) analysis.
    Checks for compliance with EU data protection requirements.
    """
    
    def __init__(self, llm_client, model: str = "gpt-4o"):
        self.llm = llm_client
        self.model = model
        self.name = "gdpr_agent"
    
    def analyze_document(self, document_text: str, document_metadata: Dict[str, Any]) -> List[ComplianceFinding]:
        """
        Analyze a document for GDPR compliance.
        
        Returns:
            List of compliance findings
        """
        
        prompt = self._build_analysis_prompt(document_text, document_metadata)
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,  # Lower temperature for consistent compliance checks
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        # Convert to ComplianceFinding objects
        findings = []
        for finding_dict in analysis.get("findings", []):
            findings.append(ComplianceFinding(
                framework="gdpr",
                finding_type=finding_dict.get("finding_type", "gap"),
                severity=finding_dict.get("severity", "medium"),
                title=finding_dict.get("title", ""),
                description=finding_dict.get("description", ""),
                location=finding_dict.get("location"),
                evidence=finding_dict.get("evidence"),
                recommendation=finding_dict.get("recommendation"),
                reasoning=finding_dict.get("reasoning")
            ))
        
        return findings
    
    def _get_system_prompt(self) -> str:
        return """You are a GDPR compliance expert. Analyze documents for compliance with the General Data Protection Regulation (GDPR).

**Key GDPR Requirements to Check:**

1. **Lawful Basis (Article 6)**: Is there a clear lawful basis for processing personal data?
2. **Data Subject Rights (Articles 15-22)**: Are procedures for data subject access, rectification, erasure, and portability documented?
3. **Data Retention (Article 5(1)(e))**: Is there an explicit data retention period?
4. **Data Minimization (Article 5(1)(c))**: Is data collection limited to what's necessary?
5. **Security Measures (Article 32)**: Are appropriate technical and organizational security measures described?
6. **Data Breach Notification (Article 33)**: Are breach notification procedures documented?
7. **Data Protection Officer (Article 37)**: If required, is a DPO designated?
8. **Cross-Border Transfers (Chapter V)**: For international transfers, are appropriate safeguards in place?
9. **Consent (Article 7)**: If consent is the lawful basis, is it freely given, specific, informed, and unambiguous?
10. **Privacy by Design (Article 25)**: Are privacy considerations integrated into processing activities?

**Severity Levels:**
- **Critical**: Clear GDPR violation that could result in significant fines (e.g., no lawful basis, no breach notification procedure)
- **High**: Important requirement missing or unclear (e.g., no data retention period, weak security measures)
- **Medium**: Best practice not followed or requirement partially met (e.g., consent mechanism unclear)
- **Low**: Minor gap or area for improvement

**Output Format (JSON):**
{
    "findings": [
        {
            "finding_type": "violation|gap|risk|compliant",
            "severity": "critical|high|medium|low",
            "title": "Brief title",
            "description": "Detailed description of the issue",
            "location": "Where in the document (page, section)",
            "evidence": "Specific text that shows the issue",
            "recommendation": "Specific action to fix",
            "reasoning": "Why this is a GDPR concern"
        }
    ],
    "overall_compliance": "compliant|partial|non_compliant",
    "summary": "Overall assessment"
}"""
    
    def _build_analysis_prompt(self, document_text: str, metadata: Dict[str, Any]) -> str:
        doc_type = metadata.get("document_type", "unknown")
        filename = metadata.get("filename", "document")
        
        return f"""Analyze this document for GDPR compliance:

**Document Type:** {doc_type}
**Filename:** {filename}

**Document Content:**
{document_text[:10000]}  # Limit to first 10k chars for MVP

Provide a comprehensive GDPR compliance analysis with specific findings, evidence, and recommendations."""


class SOC2ComplianceAgent:
    """
    Agent specialized in SOC 2 (Service Organization Control 2) analysis.
    Checks for compliance with SOC 2 Trust Service Criteria.
    """
    
    def __init__(self, llm_client, model: str = "gpt-4o"):
        self.llm = llm_client
        self.model = model
        self.name = "soc2_agent"
    
    def analyze_document(self, document_text: str, document_metadata: Dict[str, Any]) -> List[ComplianceFinding]:
        """Analyze a document for SOC 2 compliance."""
        
        prompt = self._build_analysis_prompt(document_text, document_metadata)
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        findings = []
        for finding_dict in analysis.get("findings", []):
            findings.append(ComplianceFinding(
                framework="soc2",
                finding_type=finding_dict.get("finding_type", "gap"),
                severity=finding_dict.get("severity", "medium"),
                title=finding_dict.get("title", ""),
                description=finding_dict.get("description", ""),
                location=finding_dict.get("location"),
                evidence=finding_dict.get("evidence"),
                recommendation=finding_dict.get("recommendation"),
                reasoning=finding_dict.get("reasoning")
            ))
        
        return findings
    
    def _get_system_prompt(self) -> str:
        return """You are a SOC 2 compliance expert. Analyze documents for compliance with SOC 2 Trust Service Criteria.

**SOC 2 Trust Service Criteria:**

1. **Security (Common Criteria - Required)**:
   - Access controls (logical and physical)
   - Encryption (data at rest and in transit)
   - Vulnerability management
   - Incident response procedures
   - Security monitoring and logging

2. **Availability (Optional)**:
   - System uptime and performance monitoring
   - Disaster recovery and business continuity plans
   - Backup procedures

3. **Processing Integrity (Optional)**:
   - Data processing accuracy and completeness
   - Error detection and correction
   - Quality assurance processes

4. **Confidentiality (Optional)**:
   - Data classification
   - Confidentiality agreements
   - Access restrictions for confidential data

5. **Privacy (Optional)**:
   - Privacy notice and consent
   - Data retention and disposal
   - Privacy breach procedures

**Severity Levels:**
- **Critical**: Major control gap that would fail SOC 2 audit (e.g., no encryption, no access controls)
- **High**: Important control missing or inadequate (e.g., no incident response plan)
- **Medium**: Control exists but needs improvement (e.g., incomplete backup procedures)
- **Low**: Minor gap or documentation issue

**Output Format (JSON):**
{
    "findings": [
        {
            "finding_type": "violation|gap|risk|compliant",
            "severity": "critical|high|medium|low",
            "title": "Brief title",
            "description": "Detailed description",
            "location": "Where in document",
            "evidence": "Specific text",
            "recommendation": "How to fix",
            "reasoning": "Why this matters for SOC 2"
        }
    ],
    "criteria_coverage": {
        "security": "covered|partial|missing",
        "availability": "covered|partial|missing|not_applicable",
        "processing_integrity": "covered|partial|missing|not_applicable",
        "confidentiality": "covered|partial|missing|not_applicable",
        "privacy": "covered|partial|missing|not_applicable"
    },
    "summary": "Overall assessment"
}"""
    
    def _build_analysis_prompt(self, document_text: str, metadata: Dict[str, Any]) -> str:
        doc_type = metadata.get("document_type", "unknown")
        filename = metadata.get("filename", "document")
        
        return f"""Analyze this document for SOC 2 compliance:

**Document Type:** {doc_type}
**Filename:** {filename}

**Document Content:**
{document_text[:10000]}

Provide a comprehensive SOC 2 analysis focusing on the Trust Service Criteria."""


class ContractRiskAgent:
    """
    Agent specialized in identifying legal and financial risks in contracts.
    """
    
    def __init__(self, llm_client, model: str = "gpt-4o"):
        self.llm = llm_client
        self.model = model
        self.name = "contract_risk_agent"
    
    def analyze_document(self, document_text: str, document_metadata: Dict[str, Any]) -> List[ComplianceFinding]:
        """Analyze a contract for legal and financial risks."""
        
        prompt = self._build_analysis_prompt(document_text, document_metadata)
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        analysis = json.loads(response.choices[0].message.content)
        
        findings = []
        for finding_dict in analysis.get("findings", []):
            findings.append(ComplianceFinding(
                framework="contract_risk",
                finding_type=finding_dict.get("finding_type", "risk"),
                severity=finding_dict.get("severity", "medium"),
                title=finding_dict.get("title", ""),
                description=finding_dict.get("description", ""),
                location=finding_dict.get("location"),
                evidence=finding_dict.get("evidence"),
                recommendation=finding_dict.get("recommendation"),
                reasoning=finding_dict.get("reasoning")
            ))
        
        return findings
    
    def _get_system_prompt(self) -> str:
        return """You are a contract risk analysis expert. Identify legal and financial risks in contracts and agreements.

**Common Contract Risks to Flag:**

1. **Liability Issues**:
   - Unlimited liability clauses
   - Inadequate liability caps
   - Indemnification obligations that are too broad

2. **Termination Clauses**:
   - Difficult or expensive termination terms
   - Auto-renewal without clear opt-out
   - Long notice periods

3. **Intellectual Property**:
   - Unclear IP ownership
   - Overly broad IP assignment clauses
   - Missing IP protection provisions

4. **Payment Terms**:
   - Unfavorable payment schedules
   - Hidden fees or escalation clauses
   - Currency or exchange rate risks

5. **Data and Privacy**:
   - Missing data protection clauses
   - Unclear data ownership
   - Non-compliance with GDPR/CCPA

6. **Jurisdiction and Dispute Resolution**:
   - Unfavorable jurisdiction clauses
   - Expensive arbitration requirements
   - Waiver of jury trial

7. **Performance Obligations**:
   - Unrealistic SLAs or performance guarantees
   - Penalties for non-performance
   - Vague deliverables or acceptance criteria

8. **Confidentiality**:
   - Weak confidentiality provisions
   - Overly broad disclosure permissions
   - Missing non-compete or non-solicitation clauses

**Severity Levels:**
- **Critical**: Major financial or legal risk (e.g., unlimited liability, IP loss)
- **High**: Significant risk that should be negotiated (e.g., unfavorable termination, high penalties)
- **Medium**: Moderate risk or unclear terms (e.g., vague SLAs, missing clauses)
- **Low**: Minor issue or area for clarification

**Output Format (JSON):**
{
    "findings": [
        {
            "finding_type": "risk|gap|favorable|standard",
            "severity": "critical|high|medium|low",
            "title": "Brief risk description",
            "description": "Detailed explanation of the risk",
            "location": "Section or clause number",
            "evidence": "Exact contract language",
            "recommendation": "Suggested negotiation point or revision",
            "reasoning": "Why this is a risk"
        }
    ],
    "risk_summary": {
        "total_risks": 0,
        "critical_risks": 0,
        "negotiation_priority": ["item1", "item2"]
    },
    "overall_assessment": "high_risk|moderate_risk|low_risk|acceptable"
}"""
    
    def _build_analysis_prompt(self, document_text: str, metadata: Dict[str, Any]) -> str:
        filename = metadata.get("filename", "contract")
        
        return f"""Analyze this contract for legal and financial risks:

**Contract:** {filename}

**Contract Text:**
{document_text[:10000]}

Identify all significant risks, unfavorable terms, and areas that should be negotiated. Provide specific evidence and actionable recommendations."""
