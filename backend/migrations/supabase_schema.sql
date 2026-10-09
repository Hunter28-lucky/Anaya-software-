-- =========================================================================
-- LeadQualify AI - Supabase PostgreSQL Schema & Migrations
-- Complete Tenant Isolation, Foreign Keys, Indexes, and RLS Policies
-- =========================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles Table
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'analyst',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    target_industry VARCHAR(255) DEFAULT 'Medical Tourism',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_projects_tenant ON projects(tenant_id);

-- Project Rules Table
CREATE TABLE IF NOT EXISTS project_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID UNIQUE REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
    industry_definition TEXT NOT NULL,
    inclusion_criteria JSONB DEFAULT '[]'::jsonb,
    exclusion_criteria JSONB DEFAULT '[]'::jsonb,
    positive_examples JSONB DEFAULT '[]'::jsonb,
    negative_examples JSONB DEFAULT '[]'::jsonb,
    confidence_threshold REAL DEFAULT 0.7,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Companies Table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    normalized_url VARCHAR(1024) NOT NULL,
    name VARCHAR(255),
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);

-- Import Batches Table
CREATE TABLE IF NOT EXISTS import_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    matched_rows INTEGER DEFAULT 0,
    partial_rows INTEGER DEFAULT 0,
    rejected_rows INTEGER DEFAULT 0,
    review_rows INTEGER DEFAULT 0,
    unverifiable_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'QUEUED' NOT NULL,
    column_mapping JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_import_batches_project ON import_batches(project_id);
CREATE INDEX IF NOT EXISTS idx_import_batches_status ON import_batches(status);

-- Source Records Table
CREATE TABLE IF NOT EXISTS source_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID REFERENCES import_batches(id) ON DELETE CASCADE NOT NULL,
    row_index INTEGER NOT NULL,
    original_data JSONB DEFAULT '{}'::jsonb,
    raw_company_name VARCHAR(255),
    raw_url VARCHAR(1024),
    raw_snov_result VARCHAR(255),
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_source_records_batch ON source_records(batch_id);

-- Project Records Table
CREATE TABLE IF NOT EXISTS project_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
    batch_id UUID REFERENCES import_batches(id) ON DELETE CASCADE NOT NULL,
    source_record_id UUID REFERENCES source_records(id) ON DELETE CASCADE NOT NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    final_classification VARCHAR(50) DEFAULT 'PENDING' NOT NULL,
    automated_classification VARCHAR(50) DEFAULT 'PENDING' NOT NULL,
    business_relevance VARCHAR(50) DEFAULT 'UNKNOWN',
    snov_result VARCHAR(255),
    snov_verification VARCHAR(50) DEFAULT 'INCONCLUSIVE',
    confidence REAL DEFAULT 0.0,
    evidence_quality VARCHAR(50) DEFAULT 'LOW',
    core_business_summary TEXT,
    decision_reason TEXT,
    limitations JSONB DEFAULT '[]'::jsonb,
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewer_override VARCHAR(50),
    reviewer_notes TEXT,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_project_records_project ON project_records(project_id);
CREATE INDEX IF NOT EXISTS idx_project_records_classification ON project_records(final_classification);
CREATE INDEX IF NOT EXISTS idx_project_records_reviewed ON project_records(is_reviewed);

-- Crawl Jobs Table
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(50) DEFAULT 'QUEUED' NOT NULL,
    pages_discovered INTEGER DEFAULT 0,
    pages_fetched INTEGER DEFAULT 0,
    pages_failed INTEGER DEFAULT 0,
    crawl_coverage VARCHAR(50) DEFAULT 'NONE',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_company ON crawl_jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status);

-- Crawled Pages Table
CREATE TABLE IF NOT EXISTS crawled_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crawl_job_id UUID REFERENCES crawl_jobs(id) ON DELETE CASCADE NOT NULL,
    url VARCHAR(1024) NOT NULL,
    page_type VARCHAR(50) DEFAULT 'OTHER',
    page_title VARCHAR(512),
    http_status INTEGER,
    content_hash VARCHAR(64),
    clean_text TEXT,
    tokens_estimated INTEGER DEFAULT 0,
    error_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_crawled_pages_job ON crawled_pages(crawl_job_id);

-- Evidence Items Table
CREATE TABLE IF NOT EXISTS evidence_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_record_id UUID REFERENCES project_records(id) ON DELETE CASCADE NOT NULL,
    source_url VARCHAR(1024) NOT NULL,
    page_title VARCHAR(512),
    page_type VARCHAR(50),
    excerpt TEXT NOT NULL,
    relevance VARCHAR(255),
    is_contradictory BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_project_record ON evidence_items(project_record_id);

-- Classification Runs Table
CREATE TABLE IF NOT EXISTS classification_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_record_id UUID REFERENCES project_records(id) ON DELETE CASCADE NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    prompt_version VARCHAR(50) DEFAULT '1.0.0',
    raw_output_json JSONB,
    parsed_output_json JSONB,
    tokens_prompt INTEGER DEFAULT 0,
    tokens_completion INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_classification_record ON classification_runs(project_record_id);

-- Review History Table
CREATE TABLE IF NOT EXISTS review_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_record_id UUID REFERENCES project_records(id) ON DELETE CASCADE NOT NULL,
    reviewer_id VARCHAR(255),
    previous_classification VARCHAR(50) NOT NULL,
    new_classification VARCHAR(50) NOT NULL,
    override_reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_review_history_record ON review_history(project_record_id);

-- Audit Events Table
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,
    event_type VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_events_tenant ON audit_events(tenant_id);

-- =========================================================================
-- Row Level Security (RLS) Policies
-- =========================================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_history ENABLE ROW LEVEL SECURITY;

-- Allow users to read and update their own profile
CREATE POLICY profile_access_policy ON profiles
    FOR ALL USING (auth.uid() = id);

-- Projects tenant isolation
CREATE POLICY project_tenant_policy ON projects
    FOR ALL USING (auth.uid() = tenant_id);

-- Project rules policy linked to project owner
CREATE POLICY project_rules_policy ON project_rules
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects WHERE projects.id = project_rules.project_id AND projects.tenant_id = auth.uid()
        )
    );

-- Import batches policy
CREATE POLICY import_batches_policy ON import_batches
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects WHERE projects.id = import_batches.project_id AND projects.tenant_id = auth.uid()
        )
    );

-- Project records policy
CREATE POLICY project_records_policy ON project_records
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects WHERE projects.id = project_records.project_id AND projects.tenant_id = auth.uid()
        )
    );
