from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.entities import (
    ProjectRecord,
    SourceRecord,
    Company,
    EvidenceItem,
    ReviewHistory,
    CrawlJob,
    CrawledPage,
    ClassificationRun,
)
from app.schemas.api_models import ProjectRecordOut, ReviewOverrideRequest
from app.schemas.ai_output import AIEvidenceItem

router = APIRouter()


@router.get("", response_model=List[ProjectRecordOut])
async def list_records(
    project_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    status: Optional[str] = None,
    snov_verification: Optional[str] = None,
    search: Optional[str] = None,
    is_reviewed: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ProjectRecord)
        .options(
            selectinload(ProjectRecord.source_record),
            selectinload(ProjectRecord.company).selectinload(Company.crawl_jobs),
            selectinload(ProjectRecord.evidence_items),
        )
        .order_by(desc(ProjectRecord.created_at))
    )

    filters = []
    if project_id:
        filters.append(ProjectRecord.project_id == project_id)
    if batch_id:
        filters.append(ProjectRecord.batch_id == batch_id)
    if status:
        filters.append(ProjectRecord.final_classification == status)
    if snov_verification:
        filters.append(ProjectRecord.snov_verification == snov_verification)
    if is_reviewed is not None:
        filters.append(ProjectRecord.is_reviewed == is_reviewed)

    if search:
        s = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                ProjectRecord.decision_reason.ilike(s),
                ProjectRecord.core_business_summary.ilike(s),
                ProjectRecord.snov_result.ilike(s),
            )
        )

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    records = res.scalars().all()

    out = []
    for r in records:
        src = r.source_record
        comp = r.company
        crawl = comp.crawl_jobs[0] if (comp and comp.crawl_jobs) else None

        ev_items = [
            AIEvidenceItem(
                source_url=e.source_url,
                page_title=e.page_title,
                page_type=e.page_type,
                excerpt=e.excerpt,
                relevance=e.relevance or "",
            )
            for e in r.evidence_items
        ]

        item = ProjectRecordOut(
            id=r.id,
            project_id=r.project_id,
            batch_id=r.batch_id,
            company_id=r.company_id,
            company_name=src.raw_company_name if src else (comp.name if comp else None),
            website_url=src.raw_url if src else (comp.normalized_url if comp else ""),
            domain=comp.domain if comp else None,
            final_classification=r.final_classification,
            automated_classification=r.automated_classification,
            business_relevance=r.business_relevance,
            snov_result=r.snov_result,
            snov_verification=r.snov_verification,
            confidence=r.confidence,
            evidence_quality=r.evidence_quality,
            core_business_summary=r.core_business_summary,
            decision_reason=r.decision_reason,
            limitations=r.limitations or [],
            is_reviewed=r.is_reviewed,
            reviewer_override=r.reviewer_override,
            reviewer_notes=r.reviewer_notes,
            reviewed_by=r.reviewed_by,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at,
            updated_at=r.updated_at,
            crawl_status=crawl.status if crawl else None,
            pages_discovered=crawl.pages_discovered if crawl else 0,
            pages_fetched=crawl.pages_fetched if crawl else 0,
            pages_failed=crawl.pages_failed if crawl else 0,
            crawl_coverage=crawl.crawl_coverage if crawl else None,
            evidence_items=ev_items,
        )
        out.append(item)

    return out


@router.get("/{record_id}", response_model=ProjectRecordOut)
async def get_record(record_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(ProjectRecord)
        .options(
            selectinload(ProjectRecord.source_record),
            selectinload(ProjectRecord.company).selectinload(Company.crawl_jobs),
            selectinload(ProjectRecord.evidence_items),
        )
        .where(ProjectRecord.id == record_id)
    )
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Record not found")

    src = r.source_record
    comp = r.company
    crawl = comp.crawl_jobs[0] if (comp and comp.crawl_jobs) else None

    ev_items = [
        AIEvidenceItem(
            source_url=e.source_url,
            page_title=e.page_title,
            page_type=e.page_type,
            excerpt=e.excerpt,
            relevance=e.relevance or "",
        )
        for e in r.evidence_items
    ]

    return ProjectRecordOut(
        id=r.id,
        project_id=r.project_id,
        batch_id=r.batch_id,
        company_id=r.company_id,
        company_name=src.raw_company_name if src else (comp.name if comp else None),
        website_url=src.raw_url if src else (comp.normalized_url if comp else ""),
        domain=comp.domain if comp else None,
        final_classification=r.final_classification,
        automated_classification=r.automated_classification,
        business_relevance=r.business_relevance,
        snov_result=r.snov_result,
        snov_verification=r.snov_verification,
        confidence=r.confidence,
        evidence_quality=r.evidence_quality,
        core_business_summary=r.core_business_summary,
        decision_reason=r.decision_reason,
        limitations=r.limitations or [],
        is_reviewed=r.is_reviewed,
        reviewer_override=r.reviewer_override,
        reviewer_notes=r.reviewer_notes,
        reviewed_by=r.reviewed_by,
        reviewed_at=r.reviewed_at,
        created_at=r.created_at,
        updated_at=r.updated_at,
        crawl_status=crawl.status if crawl else None,
        pages_discovered=crawl.pages_discovered if crawl else 0,
        pages_fetched=crawl.pages_fetched if crawl else 0,
        pages_failed=crawl.pages_failed if crawl else 0,
        crawl_coverage=crawl.crawl_coverage if crawl else None,
        evidence_items=ev_items,
    )


@router.post("/{record_id}/review", response_model=ProjectRecordOut)
async def review_record(
    record_id: str,
    payload: ReviewOverrideRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ProjectRecord)
        .options(
            selectinload(ProjectRecord.source_record),
            selectinload(ProjectRecord.company).selectinload(Company.crawl_jobs),
            selectinload(ProjectRecord.evidence_items),
        )
        .where(ProjectRecord.id == record_id)
    )
    res = await db.execute(stmt)
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Record not found")

    # Record history
    history = ReviewHistory(
        project_record_id=r.id,
        reviewer_id=payload.reviewer_name,
        previous_classification=r.final_classification,
        new_classification=payload.new_classification,
        override_reason=payload.override_reason,
    )
    db.add(history)

    # Update record
    r.is_reviewed = True
    r.reviewer_override = payload.new_classification
    r.reviewer_notes = payload.notes or payload.override_reason
    r.final_classification = payload.new_classification
    r.reviewed_by = payload.reviewer_name
    r.reviewed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(r)

    return await get_record(record_id, db)
