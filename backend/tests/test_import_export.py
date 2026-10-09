import io
import pandas as pd
from app.core.security import sanitize_formula_injection
from app.api.imports import detect_suggested_columns
from app.services.exporter import export_records_to_csv, export_records_to_excel


def test_sanitize_formula_injection():
    # Danger characters at beginning of cell: =, +, -, @, \t, \r, %, |
    assert sanitize_formula_injection("=cmd|'/C calc'!A0") == "'=cmd|'/C calc'!A0"
    assert sanitize_formula_injection("+123") == "'+123"
    assert sanitize_formula_injection("-SUM(A1:B2)") == "'-SUM(A1:B2)"
    assert sanitize_formula_injection("@SUM(A1:B2)") == "'@SUM(A1:B2)"
    assert sanitize_formula_injection("Safe Text") == "Safe Text"
    assert sanitize_formula_injection(123) == "123"


def test_detect_suggested_columns():
    cols = ["Organization Name", "Website URL", "Snov Status", "Country", "Notes"]
    mapping = detect_suggested_columns(cols)
    assert mapping.url_col == "Website URL"
    assert mapping.company_name_col == "Organization Name"
    assert mapping.snov_result_col == "Snov Status"
    assert mapping.location_col == "Country"


def test_export_records_csv_and_excel():
    records = [
        {
            "original_data": {"RawName": "Test Co", "RawURL": "https://test.com"},
            "company_name": "Test Co",
            "website_url": "https://test.com",
            "snov_result": "Qualified",
            "final_classification": "MATCH",
            "automated_classification": "MATCH",
            "business_relevance": "CORE",
            "snov_verification": "SUPPORTED",
            "confidence": 0.95,
            "evidence_quality": "HIGH",
            "core_business_summary": "Medical travel facilitator",
            "decision_reason": "Verified surgery packages",
            "crawl_status": "COMPLETED",
            "pages_discovered": 5,
            "pages_fetched": 5,
            "pages_failed": 0,
            "is_reviewed": False,
            "evidence_items": [
                {"source_url": "https://test.com/services", "excerpt": "Full surgery package"}
            ],
            "limitations": []
        },
        {
            "original_data": {"RawName": "=Malicious", "RawURL": "https://evil.com"},
            "company_name": "=Malicious",
            "website_url": "https://evil.com",
            "snov_result": "None",
            "final_classification": "NOT_A_MATCH",
            "automated_classification": "NOT_A_MATCH",
            "business_relevance": "INCIDENTAL",
            "snov_verification": "INCONCLUSIVE",
            "confidence": 0.88,
            "evidence_quality": "LOW",
            "core_business_summary": "Blog only",
            "decision_reason": "Editorial mention",
            "crawl_status": "COMPLETED",
            "pages_discovered": 2,
            "pages_fetched": 2,
            "pages_failed": 0,
            "is_reviewed": False,
            "evidence_items": [],
            "limitations": []
        }
    ]

    # CSV Test
    csv_bytes = export_records_to_csv(records)
    csv_str = csv_bytes.decode("utf-8")
    assert "Original_RawName" in csv_str
    assert "'=Malicious" in csv_str  # Formula injection escaped

    # Excel Test
    excel_bytes = export_records_to_excel(records)
    assert len(excel_bytes) > 1000
    # Verify openpyxl can read the sheets
    excel_file = pd.ExcelFile(io.BytesIO(excel_bytes))
    sheet_names = excel_file.sheet_names
    assert "All Records" in sheet_names
    assert "MATCH" in sheet_names
    assert "NOT_A_MATCH" in sheet_names


def test_clean_value_for_json():
    import json
    import datetime
    import numpy as np
    from app.api.imports import clean_value_for_json

    data = {
        "date": datetime.datetime(2026, 2, 10, 12, 0, 0),
        "timestamp": pd.Timestamp("2026-02-10 00:00:00"),
        "date_only": datetime.date(2026, 2, 10),
        "nan_val": float("nan"),
        "nat_val": pd.NaT,
        "int_val": np.int64(42),
        "str_val": "https://medicaltourismchina.health/",
        "nested": {"created_at": datetime.datetime(2026, 1, 1)},
    }
    cleaned = clean_value_for_json(data)
    # Ensure json.dumps does not raise any TypeError
    serialized = json.dumps(cleaned)
    assert "2026-02-10" in serialized
    assert "null" in serialized
    assert json.loads(serialized)["int_val"] == 42
