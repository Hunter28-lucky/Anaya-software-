from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from app.schemas.ai_output import AIClassificationResponse, AIEvidenceItem


# User / Profile
class ProfileCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "analyst"


class ProfileOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime


# Project Rules
class ProjectRuleCreate(BaseModel):
    industry_definition: str = Field(..., description="Precise definition of qualifying businesses in this industry")
    inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)
    positive_examples: List[Dict[str, Any]] = Field(default_factory=list)
    negative_examples: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_threshold: float = 0.70


class ProjectRuleOut(ProjectRuleCreate):
    model_config = {"from_attributes": True}

    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime


# Project
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    target_industry: str = Field(default="Medical Tourism", max_length=255)
    description: Optional[str] = None
    rules: Optional[ProjectRuleCreate] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    target_industry: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    tenant_id: str
    name: str
    target_industry: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    rules: Optional[ProjectRuleOut] = None
    total_records: int = 0
    total_batches: int = 0


# File Upload & Column Mapping Preview
class ColumnMapping(BaseModel):
    company_name_col: Optional[str] = None
    url_col: str
    snov_result_col: Optional[str] = None
    industry_col: Optional[str] = None
    location_col: Optional[str] = None
    description_col: Optional[str] = None
    custom_metadata_cols: List[str] = Field(default_factory=list)


class ParsedRecordPreview(BaseModel):
    row_number: int
    company_name: Optional[str] = None
    url: str
    is_valid_url: bool
    is_duplicate: bool
    original_row: Dict[str, Any] = Field(default_factory=dict)


class UploadPreviewResponse(BaseModel):
    filename: str
    temp_file_id: str
    available_worksheets: List[str] = Field(default_factory=list)
    selected_worksheet: str
    detected_columns: List[str]
    column_letters: Dict[str, str] = Field(default_factory=dict)
    suggested_mapping: ColumnMapping
    start_row: int = 2
    end_row: int = 2
    total_detected_rows: int
    total_non_empty_urls: int = 0
    duplicate_url_count: int = 0
    invalid_url_count: int = 0
    sample_warnings: List[str] = Field(default_factory=list)
    preview_rows: List[Dict[str, Any]] = Field(default_factory=list)
    preview_records: List[ParsedRecordPreview] = Field(default_factory=list)


class SheetPreviewRequest(BaseModel):
    temp_file_id: str
    sheet_name: str
    url_col: Optional[str] = None
    company_name_col: Optional[str] = None
    snov_result_col: Optional[str] = None
    industry_col: Optional[str] = None
    start_row: Optional[int] = None
    end_row: Optional[int] = None


class BatchStartRequest(BaseModel):
    project_id: str
    temp_file_id: str
    filename: str
    sheet_name: Optional[str] = None
    start_row: Optional[int] = 2
    end_row: Optional[int] = None
    mapping: ColumnMapping


# Batches
class BatchOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    project_id: str
    filename: str
    source_worksheet: Optional[str] = None
    source_summary: Optional[str] = None
    start_row: Optional[int] = None
    end_row: Optional[int] = None
    total_rows: int
    processed_rows: int
    matched_rows: int
    partial_rows: int
    rejected_rows: int
    review_rows: int
    unverifiable_rows: int
    failed_rows: int
    status: str
    column_mapping: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Records
class ProjectRecordOut(BaseModel):
    id: str
    project_id: str
    batch_id: str
    source_worksheet: Optional[str] = None
    row_index: Optional[int] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    website_url: str
    domain: Optional[str] = None
    final_classification: str
    automated_classification: str
    business_relevance: str
    snov_result: Optional[str] = None
    snov_verification: str
    confidence: float
    evidence_quality: str
    core_business_summary: Optional[str] = None
    decision_reason: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)
    is_reviewed: bool
    reviewer_override: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    crawl_status: Optional[str] = None
    pages_discovered: int = 0
    pages_fetched: int = 0
    pages_failed: int = 0
    crawl_coverage: Optional[str] = None
    evidence_items: List[AIEvidenceItem] = Field(default_factory=list)


# Manual Review Request
class ReviewOverrideRequest(BaseModel):
    new_classification: str = Field(..., pattern="^(MATCH|PARTIAL_MATCH|NOT_A_MATCH|NEEDS_REVIEW|UNVERIFIABLE)$")
    override_reason: str = Field(..., min_length=3)
    notes: Optional[str] = None
    reviewer_name: Optional[str] = "Reviewer"


# Stats / KPI
class ProjectStatsOut(BaseModel):
    total_imported: int
    unique_domains: int
    urls_queued: int
    websites_crawled: int
    completed_classifications: int
    match_count: int
    partial_match_count: int
    not_a_match_count: int
    needs_review_count: int
    unverifiable_count: int
    failed_jobs_count: int
    snov_supported_count: int
    snov_contradicted_count: int
    snov_inconclusive_count: int
    average_confidence: float
