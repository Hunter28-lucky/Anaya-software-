from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import ProjectRecord, ImportBatch, Company, CrawlJob
from app.schemas.api_models import ProjectStatsOut

router = APIRouter()


@router.get("", response_model=ProjectStatsOut)
async def get_project_stats(project_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    rec_filter = [ProjectRecord.project_id == project_id] if project_id else []

    total_imported = await db.scalar(
        select(func.count(ProjectRecord.id)).where(*rec_filter)
    ) or 0

    unique_domains = await db.scalar(
        select(func.count(func.distinct(ProjectRecord.company_id))).where(*rec_filter)
    ) or 0

    match_count = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.final_classification == "MATCH", *rec_filter)
    ) or 0

    partial_match_count = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.final_classification == "PARTIAL_MATCH", *rec_filter)
    ) or 0

    not_a_match_count = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.final_classification == "NOT_A_MATCH", *rec_filter)
    ) or 0

    needs_review_count = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.final_classification == "NEEDS_REVIEW", *rec_filter)
    ) or 0

    unverifiable_count = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.final_classification == "UNVERIFIABLE", *rec_filter)
    ) or 0

    snov_supported = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.snov_verification == "SUPPORTED", *rec_filter)
    ) or 0

    snov_contradicted = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.snov_verification == "CONTRADICTED", *rec_filter)
    ) or 0

    snov_inconclusive = await db.scalar(
        select(func.count(ProjectRecord.id)).where(ProjectRecord.snov_verification == "INCONCLUSIVE", *rec_filter)
    ) or 0

    avg_conf = await db.scalar(
        select(func.avg(ProjectRecord.confidence)).where(ProjectRecord.confidence > 0, *rec_filter)
    ) or 0.0

    completed_classifications = match_count + partial_match_count + not_a_match_count + needs_review_count + unverifiable_count

    # Crawl counts
    crawled_count = await db.scalar(
        select(func.count(CrawlJob.id)).where(CrawlJob.status.in_(["COMPLETED", "PARTIAL"]))
    ) or 0

    failed_crawl_count = await db.scalar(
        select(func.count(CrawlJob.id)).where(CrawlJob.status.in_(["FAILED", "BLOCKED"]))
    ) or 0

    queued_count = await db.scalar(
        select(func.count(CrawlJob.id)).where(CrawlJob.status == "QUEUED")
    ) or 0

    return ProjectStatsOut(
        total_imported=total_imported,
        unique_domains=unique_domains,
        urls_queued=queued_count,
        websites_crawled=crawled_count,
        completed_classifications=completed_classifications,
        match_count=match_count,
        partial_match_count=partial_match_count,
        not_a_match_count=not_a_match_count,
        needs_review_count=needs_review_count,
        unverifiable_count=unverifiable_count,
        failed_jobs_count=failed_crawl_count,
        snov_supported_count=snov_supported,
        snov_contradicted_count=snov_contradicted,
        snov_inconclusive_count=snov_inconclusive,
        average_confidence=round(float(avg_conf), 2),
    )
