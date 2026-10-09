export interface ProjectRule {
  id?: string;
  project_id?: string;
  industry_definition: string;
  inclusion_criteria: string[];
  exclusion_criteria: string[];
  positive_examples: Array<{ company: string; reason: string }>;
  negative_examples: Array<{ company: string; reason: string }>;
  confidence_threshold: number;
}

export interface Project {
  id: string;
  tenant_id: string;
  name: string;
  target_industry: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  rules?: ProjectRule;
  total_records: number;
  total_batches: number;
}

export interface ColumnMapping {
  company_name_col?: string;
  url_col: string;
  snov_result_col?: string;
  industry_col?: string;
  location_col?: string;
  description_col?: string;
  custom_metadata_cols?: string[];
}

export interface ParsedRecordPreview {
  row_number: number;
  company_name?: string;
  url: string;
  is_valid_url: boolean;
  is_duplicate: boolean;
  original_row: Record<string, any>;
}

export interface UploadPreviewResponse {
  filename: string;
  temp_file_id: string;
  available_worksheets: string[];
  selected_worksheet: string;
  detected_columns: string[];
  column_letters: Record<string, string>;
  suggested_mapping: ColumnMapping;
  start_row: number;
  end_row: number;
  total_detected_rows: number;
  total_non_empty_urls: number;
  duplicate_url_count: number;
  invalid_url_count: number;
  sample_warnings: string[];
  preview_rows: Record<string, any>[];
  preview_records: ParsedRecordPreview[];
}

export interface ImportBatch {
  id: string;
  project_id: string;
  filename: string;
  source_worksheet?: string;
  source_summary?: string;
  start_row?: number;
  end_row?: number;
  total_rows: number;
  processed_rows: number;
  matched_rows: number;
  partial_rows: number;
  rejected_rows: number;
  review_rows: number;
  unverifiable_rows: number;
  failed_rows: number;
  status: "QUEUED" | "PROCESSING" | "COMPLETED" | "PAUSED" | "CANCELLED" | "FAILED";
  column_mapping: Record<string, any>;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface AIEvidenceItem {
  source_url: string;
  page_title?: string;
  page_type?: string;
  excerpt: string;
  relevance: string;
}

export interface ProjectRecord {
  id: string;
  project_id: string;
  batch_id: string;
  source_worksheet?: string;
  row_index?: number;
  company_id?: string;
  company_name?: string;
  website_url: string;
  domain?: string;
  final_classification: "MATCH" | "PARTIAL_MATCH" | "NOT_A_MATCH" | "NEEDS_REVIEW" | "UNVERIFIABLE" | "PENDING";
  automated_classification: string;
  business_relevance: "CORE" | "SECONDARY" | "INCIDENTAL" | "UNKNOWN";
  snov_result?: string;
  snov_verification: "SUPPORTED" | "CONTRADICTED" | "PARTIALLY_SUPPORTED" | "INCONCLUSIVE";
  confidence: number;
  evidence_quality: "HIGH" | "MEDIUM" | "LOW";
  core_business_summary?: string;
  decision_reason?: string;
  limitations: string[];
  is_reviewed: boolean;
  reviewer_override?: string;
  reviewer_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
  crawl_status?: string;
  pages_discovered: number;
  pages_fetched: number;
  pages_failed: number;
  crawl_coverage?: string;
  evidence_items: AIEvidenceItem[];
}

export interface ProjectStats {
  total_imported: number;
  unique_domains: number;
  urls_queued: number;
  websites_crawled: number;
  completed_classifications: number;
  match_count: number;
  partial_match_count: number;
  not_a_match_count: number;
  needs_review_count: number;
  unverifiable_count: number;
  failed_jobs_count: number;
  snov_supported_count: number;
  snov_contradicted_count: number;
  snov_inconclusive_count: number;
  average_confidence: number;
}
