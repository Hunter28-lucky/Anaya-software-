import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.entities import (
    ImportBatch,
    SourceRecord,
    ProjectRecord,
    Company,
    CrawlJob,
    CrawledPage,
    EvidenceItem,
    ClassificationRun,
    ProjectRule,
)
from app.crawler.discovery import normalize_url, normalize_domain
from app.crawler.fetcher import CustomWebsiteCrawler, CrawlResult
from app.services.content_cleaner import build_compact_website_dossier
from app.services.openrouter_service import OpenRouterClient
from app.services.qualification_engine import QualificationDecisionEngine
from app.core.config import settings

logger = logging.getLogger(__name__)


class BatchExecutionRunner:
    """
    Executes an end-to-end background processing batch:
    1. Reads unverified records for batch
    2. Groups/reuses crawls by normalized domain
    3. Fetches website pages via CustomWebsiteCrawler
    4. Cleans & compresses HTML into evidence-preserving business dossier
    5. Calls OpenRouter AI
    6. Validates through QualificationDecisionEngine
    7. Writes evidence items and classification results incrementally
    """

    @classmethod
    async def process_batch(cls, batch_id: str):
        async with AsyncSessionLocal() as session:
            # 1. Fetch batch and project rules
            batch_stmt = select(ImportBatch).where(ImportBatch.id == batch_id)
            result = await session.execute(batch_stmt)
            batch = result.scalar_one_or_none()
            if not batch:
                logger.error(f"Batch {batch_id} not found")
                return

            # Fetch project rules
            rules_stmt = select(ProjectRule).where(ProjectRule.project_id == batch.project_id)
            rule_res = await session.execute(rules_stmt)
            rule = rule_res.scalar_one_or_none()
            if not rule:
                # Default Medical Tourism rule if not created yet
                rule = ProjectRule(
                    project_id=batch.project_id,
                    industry_definition="Medical tourism facilitators, international patient coordinators, and cross-border healthcare travel agencies.",
                    inclusion_criteria=[
                        "Arranges cross-border medical treatments or healthcare travel",
                        "Facilitates international patient intake, hospital coordination, and travel logistics",
                        "Offers bundled medical packages with accredited overseas hospitals"
                    ],
                    exclusion_criteria=[
                        "General travel agencies with no healthcare services",
                        "Hospitals without dedicated international patient programs",
                        "Websites that only mention medical tourism in blog articles or news"
                    ],
                    confidence_threshold=0.70
                )

            batch.status = "PROCESSING"
            await session.commit()

            # Fetch source records
            source_stmt = (
                select(SourceRecord)
                .where(SourceRecord.batch_id == batch_id)
                .order_by(SourceRecord.row_index)
            )
            source_res = await session.execute(source_stmt)
            source_records = source_res.scalars().all()

        crawler = CustomWebsiteCrawler()
        openrouter_client = OpenRouterClient()

        # Cache of crawled domains to avoid re-crawling same domain in one batch
        domain_crawl_cache: Dict[str, CrawlResult] = {}

        for src in source_records:
            # Check if batch was cancelled or paused
            async with AsyncSessionLocal() as check_session:
                b_check = await check_session.get(ImportBatch, batch_id)
                if b_check and b_check.status in ("PAUSED", "CANCELLED"):
                    logger.info(f"Batch {batch_id} halted with status {b_check.status}")
                    return

            raw_url = src.raw_url or ""
            clean_url = normalize_url(raw_url)
            domain = normalize_domain(clean_url)
            company_name = src.raw_company_name or domain or "Unknown Company"
            snov_raw = src.raw_snov_result

            crawl_result: Optional[CrawlResult] = None
            if not clean_url or not domain:
                # Missing URL record
                decision = {
                    "final_classification": "UNVERIFIABLE",
                    "automated_classification": "UNVERIFIABLE",
                    "business_relevance": "UNKNOWN",
                    "confidence": 0.0,
                    "evidence_quality": "LOW",
                    "core_business_summary": "No valid website URL supplied in import.",
                    "decision_reason": "Missing or malformed website URL.",
                    "snov_verification": "INCONCLUSIVE",
                    "review_required": True,
                    "limitations": ["No URL provided"],
                    "valid_supporting_evidence": [],
                    "valid_contradictory_evidence": [],
                }
            else:
                # 2. Crawl or reuse domain crawl cache
                if domain in domain_crawl_cache:
                    crawl_result = domain_crawl_cache[domain]
                else:
                    try:
                        crawl_result = await crawler.crawl_site(clean_url)
                        domain_crawl_cache[domain] = crawl_result
                    except Exception as e:
                        logger.error(f"Error crawling {clean_url}: {e}")
                        crawl_result = CrawlResult(
                            domain=domain,
                            starting_url=clean_url,
                            status="FAILED",
                            failure_reason=str(e),
                        )
                        domain_crawl_cache[domain] = crawl_result

                # 3. Clean and build business dossier
                dossier = build_compact_website_dossier(crawl_result.pages)

                # 4. OpenRouter AI Classification
                ai_resp = None
                ai_raw_json = None
                latency_ms = 0

                if crawl_result.status in ("COMPLETED", "PARTIAL") and dossier["total_pages"] > 0:
                    try:
                        if settings.OPENROUTER_API_KEY:
                            ai_resp, ai_raw_json, latency_ms = await openrouter_client.classify_company(
                                company_name=company_name,
                                website_url=clean_url,
                                snov_result=snov_raw,
                                rule=rule,
                                dossier_text=dossier["dossier_text"],
                            )
                        else:
                            logger.warning("OPENROUTER_API_KEY missing - running heuristic engine only")
                    except Exception as e:
                        logger.error(f"AI classification error for {clean_url}: {e}")

                # 5. Qualification Decision Engine
                decision = QualificationDecisionEngine.evaluate(
                    ai_resp=ai_resp,
                    crawl_result=crawl_result,
                    rule=rule,
                    snov_result_raw=snov_raw,
                )

            # 6. Database Persistence
            async with AsyncSessionLocal() as write_session:
                # Company entity
                comp_stmt = select(Company).where(Company.domain == domain) if domain else select(Company).where(Company.id == "none")
                comp_res = await write_session.execute(comp_stmt)
                company = comp_res.scalar_one_or_none()
                if not company and domain:
                    company = Company(
                        domain=domain,
                        normalized_url=clean_url,
                        name=company_name,
                        last_crawled_at=datetime.utcnow(),
                    )
                    write_session.add(company)
                    await write_session.flush()

                # Crawl Job entity
                crawl_job = None
                if crawl_result and company:
                    crawl_job = CrawlJob(
                        company_id=company.id,
                        status=crawl_result.status,
                        pages_discovered=crawl_result.pages_discovered,
                        pages_fetched=crawl_result.pages_fetched,
                        pages_failed=crawl_result.pages_failed,
                        crawl_coverage=crawl_result.crawl_coverage,
                        failure_reason=crawl_result.failure_reason,
                        completed_at=datetime.utcnow(),
                    )
                    write_session.add(crawl_job)
                    await write_session.flush()

                    # Save crawled pages
                    for p in crawl_result.pages:
                        page_entry = CrawledPage(
                            crawl_job_id=crawl_job.id,
                            url=p.url,
                            page_type=p.page_type,
                            page_title=p.page_title,
                            http_status=p.http_status,
                            content_hash=p.content_hash,
                            clean_text=p.clean_text,
                            tokens_estimated=p.tokens_estimated,
                            error_reason=p.error_reason,
                        )
                        write_session.add(page_entry)

                # Project Record entity
                proj_record = ProjectRecord(
                    project_id=batch.project_id,
                    batch_id=batch_id,
                    source_record_id=src.id,
                    company_id=company.id if company else None,
                    final_classification=decision["final_classification"],
                    automated_classification=decision["automated_classification"],
                    business_relevance=decision["business_relevance"],
                    snov_result=snov_raw,
                    snov_verification=decision["snov_verification"],
                    confidence=decision["confidence"],
                    evidence_quality=decision["evidence_quality"],
                    core_business_summary=decision["core_business_summary"],
                    decision_reason=decision["decision_reason"],
                    limitations=decision["limitations"],
                    is_reviewed=False,
                )
                write_session.add(proj_record)
                await write_session.flush()

                # Evidence items
                for ev in decision.get("valid_supporting_evidence", []):
                    item = EvidenceItem(
                        project_record_id=proj_record.id,
                        source_url=ev.source_url,
                        page_title=ev.page_title,
                        page_type=ev.page_type,
                        excerpt=ev.excerpt,
                        relevance=ev.relevance,
                        is_contradictory=False,
                    )
                    write_session.add(item)

                for ev in decision.get("valid_contradictory_evidence", []):
                    item = EvidenceItem(
                        project_record_id=proj_record.id,
                        source_url=ev.source_url,
                        page_title=ev.page_title,
                        page_type=ev.page_type,
                        excerpt=ev.excerpt,
                        relevance=ev.relevance,
                        is_contradictory=True,
                    )
                    write_session.add(item)

                # Classification run log
                if ai_resp:
                    run = ClassificationRun(
                        project_record_id=proj_record.id,
                        model_name=settings.OPENROUTER_MODEL,
                        prompt_version="1.2.0",
                        raw_output_json=ai_raw_json,
                        parsed_output_json=ai_resp.model_dump(),
                        latency_ms=latency_ms,
                    )
                    write_session.add(run)

                # Update batch counts
                b = await write_session.get(ImportBatch, batch_id)
                if b:
                    b.processed_rows += 1
                    status_val = decision["final_classification"]
                    if status_val == "MATCH":
                        b.matched_rows += 1
                    elif status_val == "PARTIAL_MATCH":
                        b.partial_rows += 1
                    elif status_val == "NOT_A_MATCH":
                        b.rejected_rows += 1
                    elif status_val == "NEEDS_REVIEW":
                        b.review_rows += 1
                    elif status_val == "UNVERIFIABLE":
                        b.unverifiable_rows += 1

                await write_session.commit()

        # Mark batch completed
        async with AsyncSessionLocal() as final_session:
            b = await final_session.get(ImportBatch, batch_id)
            if b:
                b.status = "COMPLETED"
                await final_session.commit()
