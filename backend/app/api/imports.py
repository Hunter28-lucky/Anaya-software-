import os
import io
import uuid
import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import ImportBatch, SourceRecord, Project
from app.schemas.api_models import UploadPreviewResponse, ColumnMapping, BatchStartRequest, BatchOut
from app.crawler.discovery import normalize_url, normalize_domain
from app.services.batch_runner import BatchExecutionRunner

router = APIRouter()

# In-memory storage for preview files during import wizard flow
UPLOAD_CACHE: Dict[str, Dict[str, Any]] = {}


def clean_value_for_json(v: Any) -> Any:
    """Recursively converts pandas/numpy/datetime types to JSON-safe primitives."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, (pd.Timestamp, datetime.datetime, datetime.date)):
        return v.isoformat()
    if isinstance(v, datetime.time):
        return v.isoformat()
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        if np.isnan(v) or np.isinf(v):
            return None
        return float(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, dict):
        return {str(k): clean_value_for_json(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [clean_value_for_json(item) for item in v]
    return str(v) if not isinstance(v, (str, int, float, bool)) else v


def detect_suggested_columns(columns: List[str]) -> ColumnMapping:
    """Intelligently detects common lead spreadsheet column names."""
    cols_clean = [str(c).strip() for c in columns]
    cols_lower = {c.lower(): c for c in cols_clean}

    url_col = ""
    for candidate in ["website", "url", "website url", "company website", "domain", "link", "web", "site"]:
        for k, original in cols_lower.items():
            if candidate == k or candidate in k.split():
                url_col = original
                break
        if url_col:
            break

    name_col = None
    for candidate in ["organization name", "company name", "company", "name", "organization", "account name", "business"]:
        for k, original in cols_lower.items():
            if candidate == k or candidate in k:
                name_col = original
                break
        if name_col:
            break

    snov_col = None
    for candidate in ["snov status", "snov result", "snov", "research result", "initial status", "snov_result", "previous status", "qualification", "status"]:
        for k, original in cols_lower.items():
            if candidate == k or candidate in k:
                snov_col = original
                break
        if snov_col:
            break

    industry_col = None
    for candidate in ["industry", "category", "sector", "vertical"]:
        for k, original in cols_lower.items():
            if candidate == k or candidate in k:
                industry_col = original
                break
        if industry_col:
            break

    location_col = None
    for candidate in ["country", "location", "city", "state", "address"]:
        for k, original in cols_lower.items():
            if candidate == k or candidate in k:
                location_col = original
                break
        if location_col:
            break

    return ColumnMapping(
        company_name_col=name_col,
        url_col=url_col or (cols_clean[0] if cols_clean else ""),
        snov_result_col=snov_col,
        industry_col=industry_col,
        location_col=location_col,
    )


@router.post("/preview", response_model=UploadPreviewResponse)
async def preview_upload(file: UploadFile = File(...)):
    """
    Accepts CSV or XLSX, reads schema, checks duplicates and URLs, returns preview.
    """
    filename = file.filename or "upload.csv"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported")

    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 25MB limit")

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded file contains no data rows")

    columns = [str(c) for c in df.columns]
    mapping = detect_suggested_columns(columns)

    # Analyze URLs if url_col identified
    url_col = mapping.url_col
    duplicate_count = 0
    invalid_count = 0
    warnings = []

    if url_col and url_col in df.columns:
        url_series = df[url_col].dropna().astype(str).str.strip()
        total_non_null = len(url_series)
        unique_urls = url_series.nunique()
        duplicate_count = total_non_null - unique_urls

        for idx, val in enumerate(url_series.head(100)):
            if not val or not ("." in val):
                invalid_count += 1

        missing_count = df[url_col].isna().sum()
        if missing_count > 0:
            warnings.append(f"{missing_count} rows have missing website URLs")
        if duplicate_count > 0:
            warnings.append(f"Detected {duplicate_count} duplicate URLs")
    else:
        warnings.append("Could not automatically identify a Website URL column. Please map it manually.")

    # Cache in memory for subsequent start-batch confirmation
    temp_id = str(uuid.uuid4())
    UPLOAD_CACHE[temp_id] = {
        "filename": filename,
        "dataframe": df,
    }

    # Prepare preview rows (first 10)
    preview_df = df.head(10)
    preview_rows = [
        {str(k): clean_value_for_json(v) for k, v in r.items()}
        for _, r in preview_df.iterrows()
    ]

    return UploadPreviewResponse(
        filename=filename,
        temp_file_id=temp_id,
        total_detected_rows=len(df),
        detected_columns=columns,
        suggested_mapping=mapping,
        preview_rows=preview_rows,
        duplicate_url_count=duplicate_count,
        invalid_url_count=invalid_count,
        sample_warnings=warnings,
    )


@router.post("/start-batch", response_model=BatchOut)
async def start_batch(
    payload: BatchStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirms column mapping, creates persistent batch & source records,
    and initiates background processing.
    """
    cached = UPLOAD_CACHE.get(payload.temp_file_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Upload session expired or file not found. Please upload again.")

    df: pd.DataFrame = cached["dataframe"]
    filename: str = payload.filename or cached["filename"]

    # Verify project exists
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    url_col = payload.mapping.url_col
    name_col = payload.mapping.company_name_col
    snov_col = payload.mapping.snov_result_col

    if url_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Mapped URL column '{url_col}' not found in file")

    # Create Batch
    batch = ImportBatch(
        project_id=payload.project_id,
        filename=filename,
        total_rows=len(df),
        status="QUEUED",
        column_mapping=payload.mapping.model_dump(),
    )
    db.add(batch)
    await db.flush()

    seen_urls = set()

    for idx, row in df.iterrows():
        raw_dict = {str(k): clean_value_for_json(v) for k, v in row.items()}
        raw_url = str(row[url_col]).strip() if pd.notna(row.get(url_col)) else ""
        raw_name = str(row[name_col]).strip() if name_col and pd.notna(row.get(name_col)) else None
        raw_snov = str(row[snov_col]).strip() if snov_col and pd.notna(row.get(snov_col)) else None

        if raw_url and raw_url.lower() in ("nan", "none", "nat"):
            raw_url = ""
        if raw_name and raw_name.lower() in ("nan", "none", "nat"):
            raw_name = None
        if raw_snov and raw_snov.lower() in ("nan", "none", "nat"):
            raw_snov = None

        is_dup = raw_url in seen_urls if raw_url else False
        if raw_url:
            seen_urls.add(raw_url)

        src_record = SourceRecord(
            batch_id=batch.id,
            row_index=idx,
            original_data=raw_dict,
            raw_company_name=raw_name,
            raw_url=raw_url,
            raw_snov_result=raw_snov,
            is_duplicate=is_dup,
        )
        db.add(src_record)

    await db.commit()
    await db.refresh(batch)

    # Launch background batch runner
    background_tasks.add_task(BatchExecutionRunner.process_batch, batch.id)

    return BatchOut.model_validate(batch)
