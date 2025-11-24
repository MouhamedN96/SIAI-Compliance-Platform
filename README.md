# SIAI Compliance Platform

Privacy-first document compliance analysis platform with conversational AI interface.

## Overview

SIAI analyzes documents for compliance violations (GDPR, SOC2, contract risks) and provides actionable remediation advice through a conversational interface. The platform learns from user feedback to improve accuracy over time.

### Key Features

- **Document Analysis**: Upload PDFs/DOCX and get instant compliance analysis
- **Conversational Interface**: Chat with the compliance agent about findings
- **Real-time Updates**: WebSocket-powered live analysis progress
- **Memory-Powered Learning**: Agent improves accuracy based on feedback
- **Tool Integrations**: Send findings to Slack, create Jira tickets via Composio
- **Privacy-First**: Self-hosted, all data stays in your infrastructure

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Next.js UI    │────────▶│   FastAPI Agent  │────────▶│   PostgreSQL    │
│  (Split-screen) │◀────────│   (WebSocket)    │◀────────│   + pgvector    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                            │
        │                            ▼
        │                    ┌──────────────────┐
        └───────────────────▶│   Composio API   │
                             │  (Slack, Jira,   │
                             │   Notion, etc.)  │
                             └──────────────────┘
```

### Components

- **Frontend**: Next.js 16 + React 19 + Tailwind CSS
- **Backend**: FastAPI + WebSocket support
- **Database**: PostgreSQL with pgvector for semantic search
- **AI**: OpenAI/Anthropic/Local LLMs (via LiteLLM)
- **Integrations**: Composio for 200+ tool connections

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (or local LLM)
- (Optional) Composio API key for integrations

### Installation

1. Clone the repository:
```bash
git clone https://github.com/MouhamedN96/SIAI-Compliance-Platform.git
cd SIAI-Compliance-Platform
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. Start services:
```bash
docker-compose up -d
```

4. Access the platform:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

### Document Analysis

1. Open the platform at http://localhost:3000
2. Drag and drop a PDF document
3. Watch real-time analysis in the conversation panel
4. Click on findings to see details in the document viewer
5. Ask follow-up questions about compliance issues

### Chat Examples

- "What are the high-severity GDPR violations?"
- "How do I fix the data retention issue?"
- "Send a summary of findings to Slack"
- "Create a Jira ticket for the SOC2 violations"

### Tool Integrations (Composio)

Enable Composio by adding your API key to `.env`:

```bash
COMPOSIO_API_KEY=your-key-here
```

Available integrations:
- Slack: Send compliance summaries
- Jira: Create tickets for violations
- Notion: Save analysis reports
- Gmail: Email findings to stakeholders
- GitHub: Track remediation in issues

## Configuration

### LLM Models

The platform supports multiple LLM providers. Edit `.env`:

```bash
# OpenAI (default)
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Anthropic (best for long documents)
LLM_MODEL=anthropic/claude-3-5-sonnet-20240620
ANTHROPIC_API_KEY=sk-ant-...

# Local (privacy-first)
LLM_MODEL=ollama/llama3
# No API key needed, point to local Ollama instance
```

### Compliance Frameworks

Supported frameworks (can be extended):
- GDPR (General Data Protection Regulation)
- SOC2 (System and Organization Controls 2)
- Contract Risk Analysis
- Custom frameworks (add to `agents/compliance_agents.py`)

## Development

### Project Structure

```
siai-compliance-platform/
├── apps/
│   ├── frontend/          # Next.js application
│   │   ├── app/           # Pages and routes
│   │   └── components/    # React components
│   └── agent-os/          # FastAPI backend
│       ├── main.py        # API server
│       └── requirements.txt
├── packages/
│   ├── database/          # Database schemas
│   ├── memory/            # Episodic/semantic memory
│   └── agents/            # Compliance agents
├── docker-compose.yml
└── README.md
```

### Running Locally (without Docker)

**Backend:**
```bash
cd apps/agent-os
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd apps/frontend
npm install
npm run dev
```

**Database:**
```bash
# Install PostgreSQL with pgvector extension
# Run schema: psql < packages/database/schema.sql
```

## API Reference

### Document Analysis

```bash
POST /api/documents/analyze-stream
Content-Type: application/json

{
  "document_id": "uuid",
  "document_text": "...",
  "filename": "contract.pdf",
  "frameworks": ["gdpr", "soc2"],
  "session_id": "websocket-session-id"
}
```

### Chat

```bash
POST /api/chat
Content-Type: application/json

{
  "session_id": "uuid",
  "message": "What are the GDPR violations?",
  "document_id": "uuid"
}
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/session-id');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'analysis_started':
      console.log('Analysis started');
      break;
    case 'finding_discovered':
      console.log('New finding:', data.finding);
      break;
    case 'analysis_complete':
      console.log('Analysis complete');
      break;
  }
};
```

## Deployment

### Production Checklist

- [ ] Change database password in `.env`
- [ ] Restrict CORS origins in `main.py`
- [ ] Enable HTTPS (use Caddy or nginx)
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Add authentication (Clerk/Auth0)
- [ ] Set up monitoring (Sentry)

### Scaling

For high-volume deployments:
- Use managed PostgreSQL (AWS RDS, Supabase)
- Deploy backend with Kubernetes
- Add Redis for session management
- Use CDN for frontend (Vercel, Cloudflare)

## License

MIT License - see LICENSE file for details.

## Support

- GitHub Issues: https://github.com/MouhamedN96/SIAI-Compliance-Platform/issues
- Documentation: https://github.com/MouhamedN96/SIAI-Compliance-Platform/wiki

