import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="analyst")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("profiles.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    target_industry = Column(String(255), default="Medical Tourism")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Profile", back_populates="projects")
    rules = relationship("ProjectRule", back_populates="project", uselist=False, cascade="all, delete-orphan")
    batches = relationship("ImportBatch", back_populates="project", cascade="all, delete-orphan")
    records = relationship("ProjectRecord", back_populates="project", cascade="all, delete-orphan")


class ProjectRule(Base):
    __tablename__ = "project_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), unique=True, nullable=False)
    industry_definition = Column(Text, nullable=False)
    inclusion_criteria = Column(JSON, default=list)  # list of str
    exclusion_criteria = Column(JSON, default=list)  # list of str
    positive_examples = Column(JSON, default=list)  # list of objects
    negative_examples = Column(JSON, default=list)  # list of objects
    confidence_threshold = Column(Float, default=0.7)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="rules")


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    matched_rows = Column(Integer, default=0)
    partial_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    review_rows = Column(Integer, default=0)
    unverifiable_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    status = Column(String(50), default="QUEUED", index=True)  # QUEUED, PROCESSING, COMPLETED, PAUSED, CANCELLED, FAILED
    column_mapping = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="batches")
    source_records = relationship("SourceRecord", back_populates="batch", cascade="all, delete-orphan")
    project_records = relationship("ProjectRecord", back_populates="batch", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    normalized_url = Column(String(1024), nullable=False)
    name = Column(String(255), nullable=True)
    last_crawled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    crawl_jobs = relationship("CrawlJob", back_populates="company", cascade="all, delete-orphan")
    project_records = relationship("ProjectRecord", back_populates="company")


class SourceRecord(Base):
    __tablename__ = "source_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    batch_id = Column(String(36), ForeignKey("import_batches.id"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    original_data = Column(JSON, default=dict)
    raw_company_name = Column(String(255), nullable=True)
    raw_url = Column(String(1024), nullable=True)
    raw_snov_result = Column(String(255), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("ImportBatch", back_populates="source_records")
    project_record = relationship("ProjectRecord", back_populates="source_record", uselist=False)


class ProjectRecord(Base):
    __tablename__ = "project_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("import_batches.id"), nullable=False, index=True)
    source_record_id = Column(String(36), ForeignKey("source_records.id"), nullable=False, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True, index=True)

    # Classification & Decision
    # MATCH, PARTIAL_MATCH, NOT_A_MATCH, NEEDS_REVIEW, UNVERIFIABLE, PENDING
    final_classification = Column(String(50), default="PENDING", index=True)
    automated_classification = Column(String(50), default="PENDING")
    business_relevance = Column(String(50), default="UNKNOWN")  # CORE, SECONDARY, INCIDENTAL, UNKNOWN
    
    # Snov cross-verification
    snov_result = Column(String(255), nullable=True)
    snov_verification = Column(String(50), default="INCONCLUSIVE")  # SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, INCONCLUSIVE
    
    confidence = Column(Float, default=0.0)
    evidence_quality = Column(String(50), default="LOW")  # HIGH, MEDIUM, LOW
    core_business_summary = Column(Text, nullable=True)
    decision_reason = Column(Text, nullable=True)
    limitations = Column(JSON, default=list)

    # Manual Review
    is_reviewed = Column(Boolean, default=False, index=True)
    reviewer_override = Column(String(50), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="records")
    batch = relationship("ImportBatch", back_populates="project_records")
    source_record = relationship("SourceRecord", back_populates="project_record")
    company = relationship("Company", back_populates="project_records")
    evidence_items = relationship("EvidenceItem", back_populates="project_record", cascade="all, delete-orphan")
    classification_runs = relationship("ClassificationRun", back_populates="project_record", cascade="all, delete-orphan")
    review_history = relationship("ReviewHistory", back_populates="project_record", cascade="all, delete-orphan")


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    # Status: QUEUED, CRAWLING, COMPLETED, PARTIAL, FAILED, BLOCKED, NO_USABLE_CONTENT
    status = Column(String(50), default="QUEUED", index=True)
    pages_discovered = Column(Integer, default=0)
    pages_fetched = Column(Integer, default=0)
    pages_failed = Column(Integer, default=0)
    crawl_coverage = Column(String(50), default="NONE")  # FULL, PARTIAL, SHALLOW, FAILED, NONE
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="crawl_jobs")
    crawled_pages = relationship("CrawledPage", back_populates="crawl_job", cascade="all, delete-orphan")


class CrawledPage(Base):
    __tablename__ = "crawled_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    crawl_job_id = Column(String(36), ForeignKey("crawl_jobs.id"), nullable=False, index=True)
    url = Column(String(1024), nullable=False, index=True)
    page_type = Column(String(50), default="OTHER")  # HOMEPAGE, ABOUT, SERVICES, CONTACT, BLOG, SITEMAP, OTHER
    page_title = Column(String(512), nullable=True)
    http_status = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)
    clean_text = Column(Text, nullable=True)
    tokens_estimated = Column(Integer, default=0)
    error_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crawl_job = relationship("CrawlJob", back_populates="crawled_pages")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_record_id = Column(String(36), ForeignKey("project_records.id"), nullable=False, index=True)
    source_url = Column(String(1024), nullable=False)
    page_title = Column(String(512), nullable=True)
    page_type = Column(String(50), nullable=True)
    excerpt = Column(Text, nullable=False)
    relevance = Column(String(255), nullable=True)
    is_contradictory = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project_record = relationship("ProjectRecord", back_populates="evidence_items")


class ClassificationRun(Base):
    __tablename__ = "classification_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_record_id = Column(String(36), ForeignKey("project_records.id"), nullable=False, index=True)
    model_name = Column(String(255), nullable=False)
    prompt_version = Column(String(50), default="1.0.0")
    raw_output_json = Column(JSON, nullable=True)
    parsed_output_json = Column(JSON, nullable=True)
    tokens_prompt = Column(Integer, default=0)
    tokens_completion = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    project_record = relationship("ProjectRecord", back_populates="classification_runs")


class ReviewHistory(Base):
    __tablename__ = "review_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_record_id = Column(String(36), ForeignKey("project_records.id"), nullable=False, index=True)
    reviewer_id = Column(String(255), nullable=True)
    previous_classification = Column(String(50), nullable=False)
    new_classification = Column(String(50), nullable=False)
    override_reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project_record = relationship("ProjectRecord", back_populates="review_history")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
