import {
  Project,
  ProjectRule,
  ImportBatch,
  ProjectRecord,
  ProjectStats,
  UploadPreviewResponse,
  ColumnMapping,
} from "@/types";

function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    let url = process.env.NEXT_PUBLIC_API_URL.trim();
    if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
      url = `https://${url}`;
    }
    return url.replace(/\/+$/, "");
  }

  if (typeof window !== "undefined") {
    if (window.location.port === "3000") {
      return "http://localhost:8008";
    }
    return "";
  }

  return "http://localhost:8008";
}

const API_BASE = getApiBase();

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function fetchCurrentUser() {
  const res = await fetch(`${API_BASE}/api/auth/me`);
  return res.json();
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/api/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function fetchProject(id: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/projects/${id}`);
  if (!res.ok) throw new Error("Failed to fetch project");
  return res.json();
}

export async function createProject(data: {
  name: string;
  target_industry: string;
  description?: string;
  rules?: Partial<ProjectRule>;
}): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function updateProjectRules(
  projectId: string,
  rules: ProjectRule
): Promise<ProjectRule> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/rules`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rules),
  });
  if (!res.ok) throw new Error("Failed to update project rules");
  return res.json();
}

export async function uploadPreview(file: File, sheetName?: string): Promise<UploadPreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (sheetName) {
    formData.append("sheet_name", sheetName);
  }

  const res = await fetch(`${API_BASE}/api/imports/preview`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function previewSheet(payload: {
  temp_file_id: string;
  sheet_name: string;
  url_col?: string;
  company_name_col?: string;
  snov_result_col?: string;
  industry_col?: string;
  start_row?: number;
  end_row?: number;
}): Promise<UploadPreviewResponse> {
  const res = await fetch(`${API_BASE}/api/imports/preview-sheet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to preview worksheet" }));
    throw new Error(err.detail || "Failed to preview worksheet");
  }
  return res.json();
}

export async function startBatch(payload: {
  project_id: string;
  temp_file_id: string;
  filename: string;
  sheet_name?: string;
  start_row?: number;
  end_row?: number;
  mapping: ColumnMapping;
}): Promise<ImportBatch> {
  const res = await fetch(`${API_BASE}/api/imports/start-batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start batch" }));
    throw new Error(err.detail || "Failed to start batch");
  }
  return res.json();
}

export async function fetchBatches(projectId?: string): Promise<ImportBatch[]> {
  const url = projectId
    ? `${API_BASE}/api/batches?project_id=${projectId}`
    : `${API_BASE}/api/batches`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch batches");
  return res.json();
}

export async function fetchBatch(batchId: string): Promise<ImportBatch> {
  const res = await fetch(`${API_BASE}/api/batches/${batchId}`);
  if (!res.ok) throw new Error("Failed to fetch batch");
  return res.json();
}

export async function pauseBatch(batchId: string): Promise<ImportBatch> {
  const res = await fetch(`${API_BASE}/api/batches/${batchId}/pause`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to pause batch");
  return res.json();
}

export async function resumeBatch(batchId: string): Promise<ImportBatch> {
  const res = await fetch(`${API_BASE}/api/batches/${batchId}/resume`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to resume batch");
  return res.json();
}

export async function cancelBatch(batchId: string): Promise<ImportBatch> {
  const res = await fetch(`${API_BASE}/api/batches/${batchId}/cancel`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to cancel batch");
  return res.json();
}

export async function fetchRecords(params: {
  project_id?: string;
  batch_id?: string;
  status?: string;
  snov_verification?: string;
  search?: string;
  is_reviewed?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ProjectRecord[]> {
  const searchParams = new URLSearchParams();
  if (params.project_id) searchParams.set("project_id", params.project_id);
  if (params.batch_id) searchParams.set("batch_id", params.batch_id);
  if (params.status && params.status !== "ALL") searchParams.set("status", params.status);
  if (params.snov_verification && params.snov_verification !== "ALL") {
    searchParams.set("snov_verification", params.snov_verification);
  }
  if (params.search) searchParams.set("search", params.search);
  if (params.is_reviewed !== undefined) searchParams.set("is_reviewed", String(params.is_reviewed));
  if (params.limit) searchParams.set("limit", String(params.limit));
  if (params.offset) searchParams.set("offset", String(params.offset));

  const res = await fetch(`${API_BASE}/api/records?${searchParams.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch records");
  return res.json();
}

export async function fetchRecord(recordId: string): Promise<ProjectRecord> {
  const res = await fetch(`${API_BASE}/api/records/${recordId}`);
  if (!res.ok) throw new Error("Failed to fetch record");
  return res.json();
}

export async function submitReviewOverride(
  recordId: string,
  payload: {
    new_classification: string;
    override_reason: string;
    notes?: string;
    reviewer_name?: string;
  }
): Promise<ProjectRecord> {
  const res = await fetch(`${API_BASE}/api/records/${recordId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit review override");
  return res.json();
}

export async function fetchStats(projectId?: string): Promise<ProjectStats> {
  const url = projectId ? `${API_BASE}/api/stats?project_id=${projectId}` : `${API_BASE}/api/stats`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch statistics");
  return res.json();
}

export function getExportDownloadUrl(projectId: string, format: "xlsx" | "csv", status?: string): string {
  const params = new URLSearchParams({ project_id: projectId, format });
  if (status && status !== "ALL") params.set("status", status);
  return `${API_BASE}/api/export/download?${params.toString()}`;
}
