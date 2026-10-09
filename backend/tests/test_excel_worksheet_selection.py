import io
import os
import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import ImportBatch, SourceRecord, ProjectRecord
from app.crawler.fetcher import CrawlResult, FetchedPage
from app.services.batch_runner import BatchExecutionRunner


def create_multi_sheet_workbook_bytes() -> bytes:
    """Creates an in-memory Excel workbook mimicking the user's multi-sheet workbook."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Sheet 1: MANUAL SEARCH
        df_manual = pd.DataFrame({
            "DATE": ["2026-01-01", "2026-01-02"],
            "WEBSITE": ["https://manual-search-agency.com", "https://another-manual.org"],
            "SIZE": ["10-50", "1-10"],
            "NOTE": ["Manual record 1", "Manual record 2"],
        })
        df_manual.to_excel(writer, sheet_name="MANUAL SEARCH ", index=False)

        # Sheet 2: SNOV SEARCH (Target Sheet)
        df_snov = pd.DataFrame({
            "name": ["HealthTravel Pro", "Global Cure Network", "Duplicate Clinic", "Duplicate Clinic"],
            "url": [
                "https://healthtravel-pro.com",
                "https://globalcure-network.org",
                "https://duplicate-clinic.com",
                "https://duplicate-clinic.com",  # Duplicate URL
            ],
            "industry": ["Medical Tourism", "Hospital & Health Care", "Clinics", "Clinics"],
            "social page": ["https://linkedin.com/ht", "https://linkedin.com/gcn", "", ""],
            "location": ["Bangkok, Thailand", "Seoul, South Korea", "Istanbul, Turkey", "Istanbul, Turkey"],
            "founded": [2015, 2018, 2020, 2020],
            "size": ["11-50", "51-200", "1-10", "1-10"],
            "hqPhone": ["+66123456", "+82234567", "+90234567", "+90234567"],
        })
        df_snov.to_excel(writer, sheet_name="SNOV SEARCH", index=False)

        # Sheet 3: NO FOUND
        df_nofound = pd.DataFrame({
            "alamedicare.com": ["https://unfound-domain-one.com", "https://unfound-domain-two.com"]
        })
        df_nofound.to_excel(writer, sheet_name="NO FOUND", index=False)

        # Sheet 4: Searching Guide
        df_guide = pd.DataFrame({
            "USA": ["Guideline 1", "Guideline 2"],
            "Canada": ["Search note A", "Search note B"],
            "Europe": ["Rules", "Tips"],
        })
        df_guide.to_excel(writer, sheet_name="Searching Guide", index=False)

    return buffer.getvalue()


async def create_test_project(client: AsyncClient, name: str = "Test Project") -> str:
    res = await client.post("/api/projects", json={
        "name": name,
        "target_industry": "Medical Tourism",
        "description": "Excel Import Selection Test"
    })
    assert res.status_code == 201, res.text
    return res.json()["id"]


@pytest.mark.asyncio
async def test_default_selection_snov_search_and_columns():
    """
    Proves:
    1. Read workbook worksheets and headers before importing.
    2. Default sheet is SNOV SEARCH.
    3. URL column defaults to column B (url).
    4. Company name column defaults to column A (name).
    5. Industry defaults to column C (industry).
    6. Start row is 2, End row is detected accurately.
    """
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        wb_bytes = create_multi_sheet_workbook_bytes()
        files = {"file": ("MEDICAL_TOURISM_TEST.xlsx", wb_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        resp = await client.post("/api/imports/preview", files=files)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # Check sheets detected
        assert "MANUAL SEARCH " in data["available_worksheets"]
        assert "SNOV SEARCH" in data["available_worksheets"]
        assert "NO FOUND" in data["available_worksheets"]
        assert "Searching Guide" in data["available_worksheets"]

        # Check default sheet is strictly SNOV SEARCH
        assert data["selected_worksheet"] == "SNOV SEARCH"

        # Check column mapping defaults
        mapping = data["suggested_mapping"]
        assert mapping["url_col"] == "url"
        assert mapping["company_name_col"] == "name"
        assert mapping["industry_col"] == "industry"

        # Check column letters (Column A = name, Column B = url, Column C = industry)
        assert data["column_letters"]["name"] == "A"
        assert data["column_letters"]["url"] == "B"
        assert data["column_letters"]["industry"] == "C"

        # Check row detection: 1 header row + 4 data rows -> rows 2 to 5
        assert data["start_row"] == 2
        assert data["end_row"] == 5
        assert data["total_detected_rows"] == 4
        assert data["total_non_empty_urls"] == 4
        assert data["duplicate_url_count"] == 1  # One duplicate URL


@pytest.mark.asyncio
async def test_strict_isolation_unselected_sheets_never_imported():
    """
    Proves:
    Only records from SNOV SEARCH column B enter the pipeline.
    URLs from MANUAL SEARCH , NO FOUND, and Searching Guide are NEVER imported.
    """
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_test_project(client, "Strict Sheet Isolation Test")
        wb_bytes = create_multi_sheet_workbook_bytes()
        files = {"file": ("WORKBOOK.xlsx", wb_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        # 1. Preview
        prev_resp = await client.post("/api/imports/preview", files=files)
        prev_data = prev_resp.json()
        temp_id = prev_data["temp_file_id"]

        # 2. Confirm & Start batch on SNOV SEARCH
        batch_payload = {
            "project_id": project_id,
            "temp_file_id": temp_id,
            "filename": "WORKBOOK.xlsx",
            "sheet_name": "SNOV SEARCH",
            "start_row": 2,
            "end_row": 5,
            "mapping": {
                "url_col": "url",
                "company_name_col": "name",
                "industry_col": "industry",
            }
        }
        start_resp = await client.post("/api/imports/start-batch", json=batch_payload)
        assert start_resp.status_code == 200, start_resp.text
        batch_id = start_resp.json()["id"]

        # 3. Verify database SourceRecords
        async with AsyncSessionLocal() as session:
            stmt = select(SourceRecord).where(SourceRecord.batch_id == batch_id)
            res = await session.execute(stmt)
            records = res.scalars().all()

            # Must have exactly 4 records from SNOV SEARCH
            assert len(records) == 4

            imported_urls = [r.raw_url for r in records]
            imported_sheets = [r.source_worksheet for r in records]

            # All source worksheets must strictly be 'SNOV SEARCH'
            assert all(s == "SNOV SEARCH" for s in imported_sheets)

            # SNOV SEARCH URLs must be present
            assert "https://healthtravel-pro.com" in imported_urls
            assert "https://globalcure-network.org" in imported_urls
            assert "https://duplicate-clinic.com" in imported_urls

            # UNSELECTED SHEETS URLS MUST NEVER BE IMPORTED!
            assert "https://manual-search-agency.com" not in imported_urls
            assert "https://another-manual.org" not in imported_urls
            assert "https://unfound-domain-one.com" not in imported_urls
            assert "https://unfound-domain-two.com" not in imported_urls

            # Traceability: Check row numbers
            row_numbers = [r.row_index for r in records]
            assert row_numbers == [2, 3, 4, 5]


@pytest.mark.asyncio
async def test_changing_sheet_changes_source_only_after_confirmation():
    """
    Proves:
    1. Switching worksheet in preview updates the preview only.
    2. No records are created in DB during preview.
    3. Crawl jobs start only after clicking Confirm & Start Processing.
    """
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_test_project(client, "Sheet Switch Test")
        wb_bytes = create_multi_sheet_workbook_bytes()
        files = {"file": ("WORKBOOK.xlsx", wb_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        
        # 1. Initial preview defaults to SNOV SEARCH
        prev_resp = await client.post("/api/imports/preview", files=files)
        prev_data = prev_resp.json()
        temp_id = prev_data["temp_file_id"]
        assert prev_data["selected_worksheet"] == "SNOV SEARCH"

        # Check DB: no batch exists yet
        async with AsyncSessionLocal() as session:
            b_stmt = select(ImportBatch).where(ImportBatch.project_id == project_id)
            batches = (await session.execute(b_stmt)).scalars().all()
            assert len(batches) == 0

        # 2. Switch sheet to 'MANUAL SEARCH ' via preview-sheet
        switch_resp = await client.post("/api/imports/preview-sheet", json={
            "temp_file_id": temp_id,
            "sheet_name": "MANUAL SEARCH ",
            "url_col": "WEBSITE",
            "company_name_col": "NOTE",
        })
        assert switch_resp.status_code == 200
        switch_data = switch_resp.json()
        assert switch_data["selected_worksheet"] == "MANUAL SEARCH "
        assert switch_data["suggested_mapping"]["url_col"] == "WEBSITE"
        assert switch_data["total_detected_rows"] == 2

        # Check DB: still NO batch exists! (Crawling does NOT start on preview)
        async with AsyncSessionLocal() as session:
            b_stmt = select(ImportBatch).where(ImportBatch.project_id == project_id)
            batches = (await session.execute(b_stmt)).scalars().all()
            assert len(batches) == 0

        # 3. Explicitly confirm and start batch with MANUAL SEARCH
        start_resp = await client.post("/api/imports/start-batch", json={
            "project_id": project_id,
            "temp_file_id": temp_id,
            "filename": "WORKBOOK.xlsx",
            "sheet_name": "MANUAL SEARCH ",
            "start_row": 2,
            "end_row": 3,
            "mapping": {
                "url_col": "WEBSITE",
                "company_name_col": "NOTE",
            }
        })
        assert start_resp.status_code == 200
        batch_id = start_resp.json()["id"]

        # Now records exist and belong ONLY to MANUAL SEARCH
        async with AsyncSessionLocal() as session:
            stmt = select(SourceRecord).where(SourceRecord.batch_id == batch_id)
            records = (await session.execute(stmt)).scalars().all()
            assert len(records) == 2
            assert all(r.source_worksheet == "MANUAL SEARCH " for r in records)
            assert any("manual-search-agency.com" in r.raw_url for r in records)
            # SNOV URLs must NOT be imported
            assert not any("healthtravel-pro.com" in r.raw_url for r in records)


@pytest.mark.asyncio
async def test_missing_worksheet_or_column_stops_processing():
    """
    Proves:
    If selected worksheet or required column does not exist, stop and return clear error (400).
    Never silently fallback.
    """
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_test_project(client, "Error Test")
        wb_bytes = create_multi_sheet_workbook_bytes()
        files = {"file": ("WORKBOOK.xlsx", wb_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        prev_resp = await client.post("/api/imports/preview", files=files)
        temp_id = prev_resp.json()["temp_file_id"]

        # 1. Missing worksheet in preview-sheet
        bad_sheet_resp = await client.post("/api/imports/preview-sheet", json={
            "temp_file_id": temp_id,
            "sheet_name": "DOES_NOT_EXIST",
        })
        assert bad_sheet_resp.status_code == 400
        assert "DOES_NOT_EXIST" in bad_sheet_resp.json()["detail"]

        # 2. Missing worksheet in start-batch
        bad_batch_sheet = await client.post("/api/imports/start-batch", json={
            "project_id": project_id,
            "temp_file_id": temp_id,
            "filename": "WORKBOOK.xlsx",
            "sheet_name": "DOES_NOT_EXIST",
            "mapping": {"url_col": "url"}
        })
        assert bad_batch_sheet.status_code == 400
        assert "DOES_NOT_EXIST" in bad_batch_sheet.json()["detail"]

        # 3. Missing column in start-batch
        bad_col_resp = await client.post("/api/imports/start-batch", json={
            "project_id": project_id,
            "temp_file_id": temp_id,
            "filename": "WORKBOOK.xlsx",
            "sheet_name": "SNOV SEARCH",
            "mapping": {"url_col": "NON_EXISTENT_URL_COLUMN"}
        })
        assert bad_col_resp.status_code == 400
        assert "NON_EXISTENT_URL_COLUMN" in bad_col_resp.json()["detail"]


@pytest.mark.asyncio
async def test_empty_cells_invalid_urls_and_duplicates():
    """
    Proves:
    Empty cells, invalid URLs, and duplicates are accurately counted and handled.
    """
    await init_db()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df = pd.DataFrame({
            "name": ["Co1", "Co2", "Co3", "Co4", "Co5"],
            "url": [
                "https://valid-one.com",
                None,                         # Empty cell
                "not-a-valid-url-without-dot", # Invalid malformed URL
                "https://valid-one.com",       # Duplicate URL
                "https://valid-two.com",
            ]
        })
        df.to_excel(writer, sheet_name="SNOV SEARCH", index=False)
    content = buffer.getvalue()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("EDGE_CASES.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = await client.post("/api/imports/preview", files=files)
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_detected_rows"] == 5
        assert data["total_non_empty_urls"] == 4  # 1 empty cell excluded
        assert data["duplicate_url_count"] == 1   # 1 duplicate
        assert data["invalid_url_count"] == 1     # 1 malformed

        # Check preview records
        preview_records = data["preview_records"]
        assert len(preview_records) == 5
        assert preview_records[0]["is_valid_url"] is True
        assert preview_records[0]["is_duplicate"] is False
        assert preview_records[1]["url"] == ""     # empty
        assert preview_records[2]["is_valid_url"] is False # malformed
        assert preview_records[3]["is_duplicate"] is True  # duplicate


@pytest.mark.asyncio
async def test_crawler_never_receives_unselected_worksheet():
    """
    Proves:
    BatchExecutionRunner and CustomWebsiteCrawler process ONLY confirmed records
    from SNOV SEARCH and never receive URLs from unselected worksheets.
    """
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await create_test_project(client, "Crawler Isolation Test")
        wb_bytes = create_multi_sheet_workbook_bytes()
        files = {"file": ("WORKBOOK.xlsx", wb_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        prev_resp = await client.post("/api/imports/preview", files=files)
        temp_id = prev_resp.json()["temp_file_id"]

        # Mock background crawler execution to intercept crawled URLs
        with patch.object(BatchExecutionRunner, "process_batch", new_callable=AsyncMock) as mock_batch_runner:
            start_resp = await client.post("/api/imports/start-batch", json={
                "project_id": project_id,
                "temp_file_id": temp_id,
                "filename": "WORKBOOK.xlsx",
                "sheet_name": "SNOV SEARCH",
                "mapping": {"url_col": "url", "company_name_col": "name", "industry_col": "industry"}
            })
            assert start_resp.status_code == 200
            batch_id = start_resp.json()["id"]

        # Now run process_batch directly with mocked crawler to inspect crawled targets
        crawled_urls = []

        async def fake_crawl(url):
            crawled_urls.append(url)
            return CrawlResult(
                domain="example.com",
                starting_url=url,
                status="COMPLETED",
                pages_discovered=1,
                pages_fetched=1,
                pages=[FetchedPage(url=url, page_type="HOME", page_title="Title", http_status=200, clean_text="Medical Tourism travel facilitation.", is_success=True)]
            )

        with patch("app.services.batch_runner.CustomWebsiteCrawler.crawl_site", side_effect=fake_crawl), \
             patch("app.services.batch_runner.OpenRouterClient.classify_company", new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {
                "decision": "MATCH",
                "confidence": 0.95,
                "business_relevance": "CORE",
                "core_business_summary": "Medical travel facilitator",
                "decision_reason": "Clear healthcare travel packages",
                "snov_status_verification": "SUPPORTED",
                "evidence_quality": "HIGH",
                "supporting_evidence": [{"url": "https://healthtravel-pro.com", "excerpt": "Medical travel", "significance": "Core"}],
                "contradictory_evidence": [],
                "limitations": []
            }

            await BatchExecutionRunner.process_batch(batch_id)

        # Verify all crawled URLs came from SNOV SEARCH
        assert len(crawled_urls) > 0
        for u in crawled_urls:
            assert "manual" not in u
            assert "unfound" not in u

        # Verify ProjectRecords created
        async with AsyncSessionLocal() as session:
            stmt = select(ProjectRecord).where(ProjectRecord.batch_id == batch_id)
            res = await session.execute(stmt)
            proj_records = res.scalars().all()

            assert len(proj_records) == 4
            for pr in proj_records:
                assert pr.source_worksheet == "SNOV SEARCH"
                assert pr.row_index in [2, 3, 4, 5]


@pytest.mark.asyncio
async def test_real_medical_tourism_workbook_if_present():
    """
    Tests against the actual '/Users/krishyogi/Desktop/MEDICAL TOURISM.xlsx' workbook:
    - Default sheet: 'SNOV SEARCH'
    - URL column: 'url' (Column B)
    - Company name column: 'name' (Column A)
    - Industry: 'industry' (Column C)
    - 1,548 data rows, start_row = 2, end_row = 1549
    - Exactly 1,548 non-empty URLs
    """
    real_path = "/Users/krishyogi/Desktop/MEDICAL TOURISM.xlsx"
    if not os.path.exists(real_path):
        pytest.skip("Real workbook not found on desktop.")

    await init_db()
    with open(real_path, "rb") as f:
        file_bytes = f.read()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("MEDICAL TOURISM.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = await client.post("/api/imports/preview", files=files)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["selected_worksheet"] == "SNOV SEARCH"
        assert data["suggested_mapping"]["url_col"] == "url"
        assert data["suggested_mapping"]["company_name_col"] == "name"
        assert data["suggested_mapping"]["industry_col"] == "industry"
        assert data["column_letters"]["name"] == "A"
        assert data["column_letters"]["url"] == "B"
        assert data["column_letters"]["industry"] == "C"

        assert data["start_row"] == 2
        assert data["end_row"] == 1549
        assert data["total_detected_rows"] == 1548
        assert data["total_non_empty_urls"] == 1548
        assert len(data["preview_records"]) == 20
        assert data["preview_records"][0]["row_number"] == 2
        assert data["preview_records"][19]["row_number"] == 21
