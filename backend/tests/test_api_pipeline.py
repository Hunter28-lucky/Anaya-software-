import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db


@pytest.mark.asyncio
async def test_health_check():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "LeadQualify AI"


@pytest.mark.asyncio
async def test_auth_profile_and_projects():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Check Profile
        prof_res = await ac.get("/api/auth/me")
        assert prof_res.status_code == 200
        assert prof_res.json()["email"] == "analyst@leadqualify.ai"

        # Create Project
        proj_payload = {
            "name": "Medical Tourism Lead Audit 2026",
            "target_industry": "Medical Tourism",
            "description": "Cross-border healthcare facilitators and coordinators audit"
        }
        create_res = await ac.post("/api/projects", json=proj_payload)
        assert create_res.status_code == 201
        project_data = create_res.json()
        project_id = project_data["id"]
        assert project_data["name"] == "Medical Tourism Lead Audit 2026"
        assert project_data["rules"] is not None

        # Fetch Projects List
        list_res = await ac.get("/api/projects")
        assert list_res.status_code == 200
        projects = list_res.json()
        assert len(projects) >= 1
        assert any(p["id"] == project_id for p in projects)

        # Update Project Rules
        new_rules = {
            "industry_definition": "International surgical concierge and overseas hospital coordination.",
            "inclusion_criteria": ["Cross border treatment logistics"],
            "exclusion_criteria": ["Generic travel portal"],
            "positive_examples": [],
            "negative_examples": [],
            "confidence_threshold": 0.75
        }
        rule_res = await ac.put(f"/api/projects/{project_id}/rules", json=new_rules)
        assert rule_res.status_code == 200
        assert rule_res.json()["confidence_threshold"] == 0.75

        # Query Stats
        stats_res = await ac.get(f"/api/stats?project_id={project_id}")
        assert stats_res.status_code == 200
        assert "completed_classifications" in stats_res.json()


@pytest.mark.asyncio
async def test_excel_with_dates_upload_and_start_batch():
    import io
    import datetime
    import pandas as pd
    from unittest.mock import patch, AsyncMock

    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create Project first
        p_res = await ac.post("/api/projects", json={
            "name": "Medical Tourism Batch Test",
            "target_industry": "Medical Tourism"
        })
        project_id = p_res.json()["id"]

        # Build Excel with datetime column like MEDICAL TOURISM.xlsx
        df = pd.DataFrame([
            {
                "DATE": datetime.datetime(2026, 2, 10, 0, 0, 0),
                "WEBSITE": "https://www.medicaltourismchina.health/",
                "SIZE": None,
                "NOTE": None,
                "Unnamed: 4": "Medical Tourism China"
            },
            {
                "DATE": datetime.datetime(2026, 2, 11, 0, 0, 0),
                "WEBSITE": "https://www.trevita.com/",
                "SIZE": "10-50",
                "NOTE": "Bariatric surgery facilitator",
                "Unnamed: 4": "Trevita Medical"
            }
        ])
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        excel_bytes = excel_buf.getvalue()

        # Preview Upload
        files = {"file": ("MEDICAL TOURISM.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        prev_res = await ac.post("/api/imports/preview", files=files)
        assert prev_res.status_code == 200
        prev_data = prev_res.json()
        temp_id = prev_data["temp_file_id"]
        assert prev_data["total_detected_rows"] == 2

        # Start Batch with patched runner
        with patch("app.api.imports.BatchExecutionRunner.process_batch", new_callable=AsyncMock):
            batch_payload = {
                "project_id": project_id,
                "temp_file_id": temp_id,
                "filename": "MEDICAL TOURISM.xlsx",
                "mapping": {
                    "company_name_col": "Unnamed: 4",
                    "url_col": "WEBSITE",
                    "snov_result_col": None,
                    "industry_col": None,
                    "location_col": None
                }
            }
            batch_res = await ac.post("/api/imports/start-batch", json=batch_payload)
            assert batch_res.status_code == 200, batch_res.text
            batch_data = batch_res.json()
            assert batch_data["id"] is not None
            assert batch_data["total_rows"] == 2
            assert batch_data["status"] == "QUEUED"
