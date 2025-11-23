-- SIAI Compliance Platform Database Schema
-- PostgreSQL 16 with pgvector extension for document embeddings

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- CORE TABLES: Document Management
-- ============================================================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(500) NOT NULL,
    original_path TEXT,
    document_type VARCHAR(100), -- 'contract', 'policy', 'agreement', 'compliance_doc', 'other'
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    upload_source VARCHAR(100), -- 'manual_upload', 'google_drive', 'dropbox', 'sharepoint'
    uploaded_by VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'analyzed', 'error'
    metadata JSONB, -- Additional document metadata
    is_archived BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);

-- ============================================================================
-- DOCUMENT CHUNKS: For vector search and embeddings
-- ============================================================================

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 embedding dimension
    page_number INTEGER,
    section_title VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- EPISODIC MEMORY: Compliance Findings
-- ============================================================================

CREATE TABLE compliance_findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    framework VARCHAR(50) NOT NULL, -- 'gdpr', 'soc2', 'hipaa', 'iso27001', 'contract_risk'
    finding_type VARCHAR(100) NOT NULL, -- 'violation', 'gap', 'risk', 'best_practice', 'compliant'
    severity VARCHAR(20) NOT NULL, -- 'critical', 'high', 'medium', 'low', 'info'
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    location TEXT, -- Where in the document (page, section)
    evidence TEXT, -- The specific text that triggered this finding
    recommendation TEXT, -- What to do about it
    agent_name VARCHAR(100), -- Which agent found this
    agent_reasoning TEXT, -- Why the agent flagged this
    user_feedback VARCHAR(20), -- 'accepted', 'rejected', 'false_positive'
    user_action_taken TEXT, -- What the user did about it
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_findings_document_id ON compliance_findings(document_id);
CREATE INDEX idx_findings_framework ON compliance_findings(framework);
CREATE INDEX idx_findings_severity ON compliance_findings(severity);
CREATE INDEX idx_findings_created_at ON compliance_findings(created_at DESC);

-- ============================================================================
-- SEMANTIC MEMORY: Risk Patterns
-- ============================================================================

CREATE TABLE risk_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_key VARCHAR(255) UNIQUE NOT NULL,
    pattern_description TEXT NOT NULL,
    framework VARCHAR(50) NOT NULL, -- 'gdpr', 'soc2', 'contract_risk', 'all'
    document_type VARCHAR(100), -- Which type of document this pattern applies to
    risk_indicator TEXT NOT NULL, -- What text/pattern indicates this risk
    frequency_observed INTEGER DEFAULT 0, -- How many times we've seen this
    true_positive_count INTEGER DEFAULT 0, -- How many times user confirmed it's a real risk
    false_positive_count INTEGER DEFAULT 0, -- How many times user said it's not a risk
    precision_score DECIMAL(5, 4), -- true_positive / (true_positive + false_positive)
    confidence_score DECIMAL(5, 4),
    avg_severity VARCHAR(20), -- Average severity of this pattern
    learned_rule TEXT, -- Human-readable rule
    remediation_template TEXT, -- Standard recommendation for this pattern
    metadata JSONB,
    first_observed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    observation_count INTEGER DEFAULT 0
);

CREATE INDEX idx_risk_patterns_framework ON risk_patterns(framework);
CREATE INDEX idx_risk_patterns_precision ON risk_patterns(precision_score DESC);

-- ============================================================================
-- COMPLIANCE SCORES: Overall document compliance
-- ============================================================================

CREATE TABLE compliance_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    framework VARCHAR(50) NOT NULL,
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    dimension_scores JSONB, -- Framework-specific dimensions
    critical_issues_count INTEGER DEFAULT 0,
    high_issues_count INTEGER DEFAULT 0,
    medium_issues_count INTEGER DEFAULT 0,
    low_issues_count INTEGER DEFAULT 0,
    compliant_items_count INTEGER DEFAULT 0,
    agent_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_compliance_scores_document_id ON compliance_scores(document_id);
CREATE INDEX idx_compliance_scores_framework ON compliance_scores(framework);
CREATE INDEX idx_compliance_scores_created_at ON compliance_scores(created_at DESC);

-- ============================================================================
-- DOCUMENT SUMMARIES: AI-generated clean summaries
-- ============================================================================

CREATE TABLE document_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    summary_type VARCHAR(50) NOT NULL, -- 'executive', 'technical', 'compliance', 'risk'
    summary_text TEXT NOT NULL,
    key_points JSONB, -- Array of key points
    action_items JSONB, -- Array of required actions
    parties_involved JSONB, -- For contracts: who are the parties
    important_dates JSONB, -- Key dates (effective date, expiration, renewal)
    financial_terms JSONB, -- Payment terms, amounts, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX idx_summaries_document_id ON document_summaries(document_id);
CREATE INDEX idx_summaries_type ON document_summaries(summary_type);

-- ============================================================================
-- ALERTS: Proactive compliance alerts
-- ============================================================================

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL, -- 'critical_risk', 'compliance_gap', 'expiring_contract', 'missing_clause'
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    recommended_action TEXT,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,
    sent_via VARCHAR(50), -- 'email', 'slack', 'jira', 'in_app'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255)
);

CREATE INDEX idx_alerts_document_id ON alerts(document_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_is_sent ON alerts(is_sent);

-- ============================================================================
-- USERS: Basic user management
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user', -- 'admin', 'compliance_officer', 'legal', 'user'
    department VARCHAR(100),
    preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- FUNCTIONS: Auto-update timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_risk_patterns_updated_at
    BEFORE UPDATE ON risk_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS: Useful aggregations
-- ============================================================================

-- View: Document compliance overview
CREATE VIEW document_compliance_overview AS
SELECT 
    d.id,
    d.filename,
    d.document_type,
    d.uploaded_at,
    d.last_analyzed_at,
    COUNT(DISTINCT cf.id) FILTER (WHERE cf.severity = 'critical') as critical_findings,
    COUNT(DISTINCT cf.id) FILTER (WHERE cf.severity = 'high') as high_findings,
    COUNT(DISTINCT cf.id) FILTER (WHERE cf.severity = 'medium') as medium_findings,
    COUNT(DISTINCT cf.id) FILTER (WHERE cf.severity = 'low') as low_findings,
    COUNT(DISTINCT a.id) FILTER (WHERE a.is_sent = FALSE) as open_alerts,
    MAX(cs.overall_score) as latest_compliance_score
FROM documents d
LEFT JOIN compliance_findings cf ON d.id = cf.document_id
LEFT JOIN alerts a ON d.id = a.document_id
LEFT JOIN compliance_scores cs ON d.id = cs.document_id
WHERE d.is_archived = FALSE
GROUP BY d.id, d.filename, d.document_type, d.uploaded_at, d.last_analyzed_at;

-- ============================================================================
-- SEED DATA: Example risk patterns
-- ============================================================================

INSERT INTO risk_patterns (pattern_key, pattern_description, framework, document_type, risk_indicator, frequency_observed, true_positive_count, false_positive_count, precision_score, confidence_score, avg_severity, learned_rule, remediation_template)
VALUES 
    ('unlimited_liability_contract', 'Unlimited liability clause in contracts', 'contract_risk', 'contract', 'unlimited liability', 45, 42, 3, 0.9333, 0.89, 'high', 'Contracts with unlimited liability clauses pose significant financial risk. 93% of flagged instances are confirmed risks.', 'Negotiate a liability cap equal to 12 months of contract value or $1M, whichever is lower.'),
    ('missing_data_retention_gdpr', 'Missing data retention period in GDPR context', 'gdpr', 'policy', 'no explicit retention period', 67, 58, 9, 0.8657, 0.92, 'medium', 'Documents lacking explicit data retention periods violate GDPR Article 5(1)(e). 87% precision.', 'Add clause: "Personal data will be retained for no longer than [X months/years] unless legally required."'),
    ('no_encryption_mention_soc2', 'No mention of encryption in SOC2 context', 'soc2', 'policy', 'no encryption at rest', 34, 30, 4, 0.8824, 0.78, 'high', 'SOC2 security controls require encryption. 88% of documents missing encryption mentions are non-compliant.', 'Add explicit encryption requirements: "All data at rest must be encrypted using AES-256 or equivalent."');
