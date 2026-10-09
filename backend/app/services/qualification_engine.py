from typing import List, Dict, Any, Optional, Set
from app.schemas.ai_output import AIClassificationResponse, AIEvidenceItem
from app.crawler.fetcher import CrawlResult
from app.models.entities import ProjectRule
from app.services.snov_verifier import evaluate_snov_agreement


class QualificationDecisionEngine:
    """
    Deterministic rule-based qualification validator that governs LLM recommendations.
    Applies strict citation verification, editorial filtering, uncertainty handling,
    and threshold enforcement.
    """

    @staticmethod
    def evaluate(
        ai_resp: Optional[AIClassificationResponse],
        crawl_result: CrawlResult,
        rule: ProjectRule,
        snov_result_raw: Optional[str] = None,
    ) -> Dict[str, Any]:
        fetched_urls: Set[str] = {p.url for p in crawl_result.pages if p.is_success}
        usable_pages = len(fetched_urls)

        # Rule 1: Website Accessibility Guard
        # An inaccessible website must remain UNVERIFIABLE. Never auto-reject.
        if usable_pages == 0:
            snov_agree, snov_expl = evaluate_snov_agreement(snov_result_raw, "UNVERIFIABLE", "UNKNOWN")
            return {
                "final_classification": "UNVERIFIABLE",
                "automated_classification": "UNVERIFIABLE",
                "business_relevance": "UNKNOWN",
                "confidence": 0.0,
                "evidence_quality": "LOW",
                "core_business_summary": "Website could not be accessed or contained no usable content.",
                "decision_reason": f"Crawl failed or blocked: {crawl_result.failure_reason or 'No usable pages fetched'}.",
                "snov_verification": snov_agree,
                "review_required": True,
                "limitations": ["Site inaccessible or blocked during crawl"],
                "valid_supporting_evidence": [],
                "valid_contradictory_evidence": [],
            }

        # If AI response failed or is absent
        if not ai_resp:
            snov_agree, snov_expl = evaluate_snov_agreement(snov_result_raw, "NEEDS_REVIEW", "UNKNOWN")
            return {
                "final_classification": "NEEDS_REVIEW",
                "automated_classification": "NEEDS_REVIEW",
                "business_relevance": "UNKNOWN",
                "confidence": 0.2,
                "evidence_quality": "LOW",
                "core_business_summary": "AI classification could not be completed.",
                "decision_reason": "AI evaluation failed or returned invalid response.",
                "snov_verification": snov_agree,
                "review_required": True,
                "limitations": ["AI classification unavailable"],
                "valid_supporting_evidence": [],
                "valid_contradictory_evidence": [],
            }

        # Rule 2: Citation Anti-Hallucination Guard
        # Only accept evidence URLs that exist in the fetched-page records.
        valid_supporting: List[AIEvidenceItem] = []
        hallucinated_citations = 0

        for item in ai_resp.supporting_evidence:
            if item.source_url in fetched_urls:
                valid_supporting.append(item)
            else:
                hallucinated_citations += 1

        valid_contradictory: List[AIEvidenceItem] = []
        for item in ai_resp.contradictory_evidence:
            if item.source_url in fetched_urls:
                valid_contradictory.append(item)
            else:
                hallucinated_citations += 1

        limitations = list(ai_resp.limitations or [])
        if hallucinated_citations > 0:
            limitations.append(f"Model cited {hallucinated_citations} URLs not present in fetched crawl records")

        # Rule 3: Blog-Only & Incidental False Positive Guard
        # A keyword match in a blog post does NOT qualify a business.
        is_only_blog_evidence = False
        if valid_supporting:
            all_blog = all((item.page_type == "BLOG" or "/blog" in item.source_url.lower()) for item in valid_supporting)
            if all_blog:
                is_only_blog_evidence = True

        raw_classification = ai_resp.classification
        raw_relevance = ai_resp.business_relevance
        confidence = float(ai_resp.confidence)
        threshold = float(rule.confidence_threshold if rule else 0.70)
        review_required = ai_resp.review_required

        final_status = raw_classification
        decision_reason = ai_resp.reason

        # Deterministic Overrides
        if is_only_blog_evidence or raw_relevance == "INCIDENTAL":
            if raw_classification in ("MATCH", "PARTIAL_MATCH"):
                final_status = "NOT_A_MATCH"
                raw_relevance = "INCIDENTAL"
                decision_reason = (
                    "Incidental mention detected: Topic is discussed only in editorial/blog content "
                    "without commercial service provision."
                )
                review_required = True

        # Conflicting Evidence Guard
        if valid_contradictory and len(valid_contradictory) > 0 and final_status == "MATCH":
            final_status = "NEEDS_REVIEW"
            decision_reason = f"Conflicting evidence present: {valid_contradictory[0].excerpt[:150]}"
            review_required = True

        # Confidence Threshold Guard
        if confidence < threshold and final_status in ("MATCH", "PARTIAL_MATCH"):
            final_status = "NEEDS_REVIEW"
            decision_reason = f"Confidence score ({confidence:.2f}) falls below required threshold ({threshold:.2f})."
            review_required = True

        # Hallucination Guard
        if hallucinated_citations > 0 and not valid_supporting and final_status == "MATCH":
            final_status = "NEEDS_REVIEW"
            decision_reason = "Model claimed MATCH but provided no valid citations from actual fetched pages."
            review_required = True

        # Crawl Coverage Guard
        if crawl_result.crawl_coverage == "SHALLOW" and final_status == "NOT_A_MATCH" and usable_pages == 1:
            # If only 1 page was fetched and it was shallow, mark as NEEDS_REVIEW unless homepage explicitly states an entirely different business
            if raw_relevance == "UNKNOWN":
                final_status = "NEEDS_REVIEW"
                limitations.append("Only homepage crawled; insufficient coverage to safely reject")
                review_required = True

        # Snov Cross-Verification
        snov_agreement, snov_expl = evaluate_snov_agreement(snov_result_raw, final_status, raw_relevance)

        return {
            "final_classification": final_status,
            "automated_classification": raw_classification,
            "business_relevance": raw_relevance,
            "confidence": confidence,
            "evidence_quality": ai_resp.evidence_quality,
            "core_business_summary": ai_resp.core_business_summary,
            "decision_reason": decision_reason,
            "snov_verification": snov_agreement,
            "review_required": review_required,
            "limitations": limitations,
            "valid_supporting_evidence": valid_supporting,
            "valid_contradictory_evidence": valid_contradictory,
        }
