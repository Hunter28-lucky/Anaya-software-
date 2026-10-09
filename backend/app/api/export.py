from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.entities import ProjectRecord, SourceRecord, Company, EvidenceItem
from app.services.exporter import export_records_to_csv, export_records_to_excel

router = APIRouter()


@router.get("/download")
async def export_project_records(
    project_id: str,
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ProjectRecord)
        .options(
            selectinload(ProjectRecord.source_record),
            selectinload(ProjectRecord.company).selectinload(Company.crawl_jobs),
            selectinload(ProjectRecord.evidence_items),
        )
        .where(ProjectRecord.project_id == project_id)
    )

    if status and status != "ALL":
        stmt = stmt.where(ProjectRecord.final_classification == status)

    res = await db.execute(stmt)
    records = res.scalars().all()

    # Flatten records for export
    flattened = []
    for r in records:
        src = r.source_record
        comp = r.company
        crawl = comp.crawl_jobs[0] if (comp and comp.crawl_jobs) else None
        ev_list = [{"source_url": e.source_url, "excerpt": e.excerpt} for e in r.evidence_items]

        flattened.append({
            "original_data": src.original_data if src else {},
            "source_worksheet": r.source_worksheet or (src.source_worksheet if src else ""),
            "row_index": r.row_index or (src.row_index if src else ""),
            "company_name": src.raw_company_name if src else (comp.name if comp else ""),
            "website_url": src.raw_url if src else (comp.normalized_url if comp else ""),
            "snov_result": r.snov_result,
            "final_classification": r.final_classification,
            "automated_classification": r.automated_classification,
            "business_relevance": r.business_relevance,
            "snov_verification": r.snov_verification,
            "confidence": r.confidence,
            "evidence_quality": r.evidence_quality,
            "core_business_summary": r.core_business_summary,
            "decision_reason": r.decision_reason,
            "crawl_status": crawl.status if crawl else "UNKNOWN",
            "pages_discovered": crawl.pages_discovered if crawl else 0,
            "pages_fetched": crawl.pages_fetched if crawl else 0,
            "pages_failed": crawl.pages_failed if crawl else 0,
            "is_reviewed": r.is_reviewed,
            "reviewer_override": r.reviewer_override,
            "reviewer_notes": r.reviewer_notes,
            "limitations": r.limitations,
            "evidence_items": ev_list,
        })

    filename_suffix = f"_{status.lower()}" if status and status != "ALL" else "_all"
    if format == "csv":
        csv_bytes = export_records_to_csv(flattened)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="leadqualify_export{filename_suffix}.csv"'}
        )
    else:
        xlsx_bytes = export_records_to_excel(flattened)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="leadqualify_export{filename_suffix}.xlsx"'}
        )
