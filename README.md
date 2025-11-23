# SIAI Compliance Platform

**Privacy-First AI-Powered Document Compliance & Risk Analysis**

An intelligent platform that instantly analyzes documents, extracts key information, flags compliance risks, and delivers clean summaries. Built for compliance officers, legal teams, and auditors who need fast, accurate document analysis.

---

## 🎯 What This Does

SIAI (Secure Intelligence & Audit Interface) transforms document review from hours to seconds by:

1. **Analyzing compliance** against GDPR, SOC 2, HIPAA, ISO 27001, and custom frameworks
2. **Identifying legal and financial risks** in contracts and agreements
3. **Extracting key information** (parties, dates, obligations, payment terms)
4. **Generating clean summaries** for executives and stakeholders
5. **Learning from feedback** to improve accuracy over time

### Key Differentiators

- **Privacy-First**: Self-hosted, your documents never leave your infrastructure
- **Multi-Framework**: GDPR, SOC 2, contract risk analysis (extensible to HIPAA, ISO 27001, etc.)
- **Memory-Powered Learning**: Gets smarter with every document analyzed
- **Actionable Insights**: Not just problems—specific recommendations for remediation
- **Model-Agnostic**: Works with any LLM (OpenAI, Anthropic, local models)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│           Document Upload + Analysis Dashboard               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Agent Backend (FastAPI)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       Document Analyst Agent (Orchestrator)          │  │
│  │                                                       │  │
│  │  Perceive → Plan → Act → Reflect Loop                │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                    │
│         ┌───────────────┼───────────────┐                   │
│         │               │               │                   │
│  ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐            │
│  │    GDPR     │ │   SOC 2   │ │  Contract   │            │
│  │    Agent    │ │   Agent   │ │Risk Agent   │            │
│  └─────────────┘ └───────────┘ └──────┬──────┘            │
│                                        │                    │
└────────────────────────────────────────┼────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────┐
              │                          │                  │
       ┌──────▼──────┐          ┌───────▼────────┐  ┌──────▼──────┐
       │  PostgreSQL │          │ Episodic Memory│  │  Semantic   │
       │  + pgvector │          │   (Findings)   │  │   Memory    │
       └─────────────┘          └────────────────┘  │  (Patterns) │
                                                     └─────────────┘
```

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 14 + TypeScript | Document upload and analysis dashboard |
| **Agent Backend** | FastAPI + Python | REST API and agent orchestration |
| **Document Analyst** | Custom Agent | Main orchestrator (perceive-plan-act-reflect) |
| **GDPR Agent** | LLM-powered | Analyzes GDPR compliance |
| **SOC 2 Agent** | LLM-powered | Analyzes SOC 2 trust service criteria |
| **Contract Risk Agent** | LLM-powered | Identifies legal and financial risks |
| **Memory System** | PostgreSQL | Dual memory (episodic + semantic) |
| **Database** | PostgreSQL 16 + pgvector | Stores documents, findings, patterns |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (or other LLM provider)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd siai-compliance-platform

# Create .env file
cat > .env << EOF
# Database
DB_PASSWORD=your_secure_password

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4o
EOF
```

### 2. Start the Platform

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Agent Backend API (port 8000)
- Frontend Dashboard (port 3000)

### 3. Access the Platform

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📖 Usage

### Analyze a Document (via API)

```bash
curl -X POST http://localhost:8000/api/documents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_001",
    "document_text": "This Privacy Policy describes how we collect, use, and share personal data...",
    "filename": "privacy_policy.txt",
    "document_type": "policy",
    "frameworks": ["gdpr", "soc2"]
  }'
```

**Response:**

```json
{
  "document_id": "doc_001",
  "analysis_timestamp": "2025-01-20T10:30:00",
  "frameworks_analyzed": ["gdpr", "soc2"],
  "findings": [
    {
      "framework": "gdpr",
      "finding_type": "gap",
      "severity": "high",
      "title": "Missing data retention period",
      "description": "The policy does not specify how long personal data will be retained, violating GDPR Article 5(1)(e).",
      "location": "Section 3: Data Usage",
      "evidence": "We collect and use your data for our services...",
      "recommendation": "Add explicit retention period: 'Personal data will be retained for no longer than 24 months unless legally required.'",
      "reasoning": "GDPR requires explicit data retention periods to ensure data is not kept longer than necessary."
    },
    {
      "framework": "soc2",
      "finding_type": "gap",
      "severity": "critical",
      "title": "No mention of encryption",
      "description": "The policy does not mention encryption of data at rest or in transit.",
      "location": "Section 4: Security",
      "evidence": "We implement security measures to protect your data...",
      "recommendation": "Add: 'All data is encrypted at rest using AES-256 and in transit using TLS 1.3.'",
      "reasoning": "SOC 2 security criteria require explicit encryption controls."
    }
  ],
  "summary": {
    "document_name": "privacy_policy.txt",
    "document_type": "policy",
    "total_findings": 2,
    "critical_issues": 1,
    "high_issues": 1,
    "medium_issues": 0,
    "low_issues": 0,
    "top_risks": [
      {
        "title": "No mention of encryption",
        "severity": "critical",
        "recommendation": "Add: 'All data is encrypted at rest using AES-256 and in transit using TLS 1.3.'"
      }
    ],
    "overall_assessment": "high_risk"
  },
  "risk_score": 40,
  "learned_patterns_applied": [
    {
      "pattern_key": "missing_data_retention_gdpr",
      "precision": 0.87,
      "risk_indicator": "no explicit retention period",
      "remediation": "Add clause: 'Personal data will be retained for no longer than [X months/years] unless legally required.'"
    }
  ],
  "actions_taken": [
    "GDPR compliance analysis completed",
    "SOC 2 compliance analysis completed",
    "Executive summary generated",
    "Applied 1 learned patterns"
  ]
}
```

### Upload and Analyze a Document

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@contract.txt" \
  -F "document_type=contract" \
  -F "frameworks=contract_risk"
```

### View Document Findings

```bash
curl http://localhost:8000/api/documents/doc_001/findings?severity=critical
```

### Get Document Risk Profile

```bash
curl http://localhost:8000/api/documents/doc_001/risk-profile
```

### Submit Feedback (for Learning)

```bash
curl -X POST http://localhost:8000/api/findings/finding_123/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "finding_id": "finding_123",
    "feedback": "accepted",
    "action_taken": "Updated policy to include data retention period"
  }'
```

### View Learned Patterns

```bash
curl http://localhost:8000/api/patterns?framework=gdpr
```

---

## 🧠 How the Agent Learns

SIAI implements a **dual-memory architecture**:

### 1. Episodic Memory (Specific Findings)

Stores every compliance finding:
- What document was analyzed?
- What framework was applied?
- What was the finding? (severity, description, evidence)
- Did the user accept or reject it?

**Example:**
```json
{
  "document_id": "doc_001",
  "framework": "gdpr",
  "finding_type": "gap",
  "severity": "high",
  "title": "Missing data retention period",
  "user_feedback": "accepted",
  "user_action_taken": "Updated policy"
}
```

### 2. Semantic Memory (Generalized Patterns)

Learns patterns across all documents:
- "Documents lacking explicit data retention periods violate GDPR Article 5(1)(e). 87% precision."
- "Contracts with unlimited liability clauses pose significant financial risk. 93% precision."
- "SOC 2 security controls require encryption. 88% of documents missing encryption mentions are non-compliant."

**Example:**
```json
{
  "pattern_key": "unlimited_liability_contract",
  "precision_score": 0.93,
  "frequency_observed": 45,
  "true_positive_count": 42,
  "false_positive_count": 3,
  "learned_rule": "Contracts with unlimited liability clauses pose significant financial risk. 93% of flagged instances are confirmed risks.",
  "remediation_template": "Negotiate a liability cap equal to 12 months of contract value or $1M, whichever is lower."
}
```

### 3. Continuous Improvement

The agent improves over time:
- **Session 1**: Applies generic compliance rules
- **Session 10**: Notices patterns specific to your organization
- **Session 50**: Provides highly personalized recommendations based on what works for YOUR documents

---

## 🔧 Configuration

### LLM Models

The platform is **model-agnostic**. Change the model in `.env`:

```bash
# OpenAI GPT-4o (recommended for compliance)
LLM_MODEL=gpt-4o

# Anthropic Claude 3.5 Sonnet (best for long documents)
LLM_MODEL=anthropic/claude-3-5-sonnet-20240620

# Local model via Ollama (for privacy)
LLM_MODEL=ollama/llama3

# Groq (for speed)
LLM_MODEL=groq/llama3-70b-8192
```

### Supported Frameworks

Current frameworks (MVP):
- **GDPR**: EU data protection regulation
- **SOC 2**: Trust service criteria (security, availability, etc.)
- **Contract Risk**: Legal and financial risks in contracts

**Coming soon:**
- HIPAA (healthcare)
- ISO 27001 (information security)
- CCPA (California privacy)
- PCI DSS (payment card security)

### Adding a New Framework

1. Create a new agent in `packages/agents/compliance_agents.py`:

```python
class HIPAAComplianceAgent:
    def analyze_document(self, document_text, metadata):
        # Implement HIPAA analysis
        pass
```

2. Register it in `document_analyst.py`:

```python
self.hipaa_agent = HIPAAComplianceAgent(llm_client, model)
```

3. Add to the plan in the `plan()` method.

---

## 📊 Database Schema

### Core Tables

- **documents**: Uploaded documents and metadata
- **document_chunks**: Document chunks with embeddings (for vector search)
- **compliance_findings**: Episodic memory (specific findings)
- **risk_patterns**: Semantic memory (learned patterns)
- **compliance_scores**: Overall compliance scores per framework
- **document_summaries**: AI-generated summaries
- **alerts**: Proactive compliance alerts

See `packages/database/schema.sql` for full schema.

---

## 🎨 Customization

### White-Label Deployment

The platform is designed to be white-labeled:
- Change branding in `.env` (logo, colors, company name)
- Modular agents (easy to add/remove frameworks)
- Multi-tenancy ready (database schema supports multiple customers)

### Integration with Existing Tools

Use Composio to integrate with:
- **Google Drive / Dropbox**: Auto-analyze documents as they're uploaded
- **Slack**: Send compliance alerts to channels
- **Jira**: Create tickets for critical findings
- **Notion**: Save summaries to knowledge base

---

## 🧪 Testing

### Run Unit Tests

```bash
cd apps/agent-os
pytest tests/
```

### Test the Agent Loop

```python
from agents.document_analyst import DocumentAnalystAgent
from memory.compliance_memory import ComplianceMemoryAgent

# Initialize
memory = ComplianceMemoryAgent(DATABASE_URL)
agent = DocumentAnalystAgent(llm_client, memory)

# Test analysis
result = agent.analyze_document(
    document_id="test_doc",
    document_text="Your document text here...",
    document_metadata={"filename": "test.txt", "document_type": "policy"},
    frameworks=["gdpr"]
)

print(result)
```

---

## 📦 Deployment

### Production Deployment

1. **Use environment-specific configs**:
   - Production `.env` with strong passwords
   - Restrict CORS origins in `main.py`

2. **Scale with Docker Swarm or Kubernetes**:
   ```bash
   docker stack deploy -c docker-compose.yml siai
   ```

3. **Add authentication** (e.g., Clerk, Auth0)

4. **Set up monitoring** (Prometheus, Grafana)

### Cloud Deployment

The platform can be deployed on:
- **AWS**: ECS + RDS + S3
- **GCP**: Cloud Run + Cloud SQL
- **Azure**: Container Instances + PostgreSQL

---

## 🤝 Contributing

This is an open-source project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🆘 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

## 🎯 Roadmap

- [ ] Add HIPAA, ISO 27001, CCPA frameworks
- [ ] PDF and DOCX parsing (currently text-only)
- [ ] Vector search for similar documents
- [ ] Multi-language support
- [ ] Chrome extension for inline document analysis
- [ ] Bulk document analysis
- [ ] Custom compliance frameworks (user-defined rules)

---

**Built with ❤️ for compliance officers, legal teams, and auditors who deserve better tools.**
