import io
import pandas as pd
from typing import List, Dict, Any, Optional
from app.core.security import sanitize_formula_injection


def prepare_export_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms database record objects into flattened, formula-injection-safe export dictionaries.
    """
    clean_rows = []
    for r in records:
        evidence_urls = "; ".join([e.get("source_url", "") for e in r.get("evidence_items", []) if e.get("source_url")])
        evidence_excerpts = " | ".join([f'"{e.get("excerpt", "")}"' for e in r.get("evidence_items", []) if e.get("excerpt")])
        limitations_str = "; ".join(r.get("limitations", []) or [])

        # Start with original imported data columns if available
        original = r.get("original_data", {}) or {}
        row = {}
        for k, v in original.items():
            row[f"Original_{k}"] = sanitize_formula_injection(v)

        # Standard qualification output columns
        row["Source Worksheet"] = sanitize_formula_injection(r.get("source_worksheet", ""))
        row["Source Row Index"] = r.get("row_index", "")
        row["Company Name"] = sanitize_formula_injection(r.get("company_name", ""))
        row["Website URL"] = sanitize_formula_injection(r.get("website_url", ""))
        row["Original Snov Result"] = sanitize_formula_injection(r.get("snov_result", ""))
        row["Final Classification"] = sanitize_formula_injection(r.get("final_classification", ""))
        row["Automated Classification"] = sanitize_formula_injection(r.get("automated_classification", ""))
        row["Business Relevance"] = sanitize_formula_injection(r.get("business_relevance", ""))
        row["Snov Verification"] = sanitize_formula_injection(r.get("snov_verification", ""))
        row["Confidence"] = r.get("confidence", 0.0)
        row["Evidence Quality"] = sanitize_formula_injection(r.get("evidence_quality", ""))
        row["Core Business Summary"] = sanitize_formula_injection(r.get("core_business_summary", ""))
        row["Decision Reason"] = sanitize_formula_injection(r.get("decision_reason", ""))
        row["Evidence URLs"] = sanitize_formula_injection(evidence_urls)
        row["Evidence Excerpts"] = sanitize_formula_injection(evidence_excerpts)
        row["Crawl Status"] = sanitize_formula_injection(r.get("crawl_status", "UNKNOWN"))
        row["Pages Discovered"] = r.get("pages_discovered", 0)
        row["Pages Fetched"] = r.get("pages_fetched", 0)
        row["Pages Failed"] = r.get("pages_failed", 0)
        row["Is Reviewed"] = r.get("is_reviewed", False)
        row["Reviewer Override"] = sanitize_formula_injection(r.get("reviewer_override", ""))
        row["Reviewer Notes"] = sanitize_formula_injection(r.get("reviewer_notes", ""))
        row["Limitations"] = sanitize_formula_injection(limitations_str)

        clean_rows.append(row)
    return clean_rows


def export_records_to_csv(records: List[Dict[str, Any]]) -> bytes:
    """Generate CSV bytes safely escaped against formula injection."""
    cleaned = prepare_export_records(records)
    df = pd.DataFrame(cleaned)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue().encode("utf-8")


def export_records_to_excel(records: List[Dict[str, Any]]) -> bytes:
    """
    Generate XLSX workbook with multiple sheets divided by classification status.
    """
    cleaned = prepare_export_records(records)
    df_all = pd.DataFrame(cleaned)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # All records sheet
        if df_all.empty:
            pd.DataFrame([{"Message": "No records found"}]).to_excel(writer, sheet_name="All Records", index=False)
        else:
            df_all.to_excel(writer, sheet_name="All Records", index=False)

            # Categorized sheets
            for status in ["MATCH", "PARTIAL_MATCH", "NOT_A_MATCH", "NEEDS_REVIEW", "UNVERIFIABLE"]:
                if "Final Classification" in df_all.columns:
                    filtered = df_all[df_all["Final Classification"] == status]
                    if not filtered.empty:
                        sheet_title = status[:31]  # Excel max sheet name is 31 chars
                        filtered.to_excel(writer, sheet_name=sheet_title, index=False)

    return output.getvalue()
