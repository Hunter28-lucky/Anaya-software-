from app.schemas.ai_output import AIClassificationResponse, AIEvidenceItem
from app.crawler.fetcher import CrawlResult, FetchedPage
from app.models.entities import ProjectRule
from app.services.qualification_engine import QualificationDecisionEngine


def get_sample_rule():
    return ProjectRule(
        industry_definition="Medical tourism facilitators and cross-border healthcare coordinators.",
        inclusion_criteria=["Facilitates overseas surgery", "Coordinates international patient travel"],
        exclusion_criteria=["Blog only", "General travel agency without medical partnerships"],
        confidence_threshold=0.70
    )


def test_genuine_medical_tourism_provider_qualifies():
    crawl_res = CrawlResult(
        domain="globalcare.com",
        starting_url="https://globalcare.com",
        status="COMPLETED",
        pages_discovered=4,
        pages_fetched=4,
        crawl_coverage="FULL",
        pages=[
            FetchedPage(url="https://globalcare.com", page_type="HOMEPAGE", is_success=True),
            FetchedPage(url="https://globalcare.com/services", page_type="SERVICES", is_success=True),
        ]
    )

    ai_resp = AIClassificationResponse(
        company_name="Global Care",
        website_url="https://globalcare.com",
        core_business_summary="Cross-border medical surgery facilitation and concierge coordination.",
        primary_services=["Medical travel arrangements", "Hospital admission coordination"],
        customer_types=["International patients seeking elective surgery"],
        target_category="Medical Tourism",
        business_relevance="CORE",
        classification="MATCH",
        confidence=0.92,
        evidence_quality="HIGH",
        supporting_evidence=[
            AIEvidenceItem(
                source_url="https://globalcare.com/services",
                page_title="Services",
                page_type="SERVICES",
                excerpt="We coordinate surgery in JCI accredited hospitals in Bangkok including travel and recovery packages.",
                relevance="Shows core medical travel service"
            )
        ],
        contradictory_evidence=[],
        reason="Genuine facilitator offering comprehensive overseas treatment coordination.",
        review_required=False,
    )

    decision = QualificationDecisionEngine.evaluate(
        ai_resp=ai_resp,
        crawl_result=crawl_res,
        rule=get_sample_rule(),
        snov_result_raw="Qualified"
    )

    assert decision["final_classification"] == "MATCH"
    assert decision["business_relevance"] == "CORE"
    assert decision["snov_verification"] == "SUPPORTED"
    assert len(decision["valid_supporting_evidence"]) == 1


def test_blog_only_incidental_mention_is_overridden_to_not_a_match():
    """A company that merely blogs about medical tourism must NOT qualify as a provider."""
    crawl_res = CrawlResult(
        domain="travelblogger.com",
        starting_url="https://travelblogger.com",
        status="COMPLETED",
        pages=[
            FetchedPage(url="https://travelblogger.com/blog/medical-tourism-tips", page_type="BLOG", is_success=True),
        ]
    )

    # Even if AI output suggested MATCH, our deterministic engine catches blog-only citation / incidental relevance!
    ai_resp = AIClassificationResponse(
        company_name="Travel Blogger",
        website_url="https://travelblogger.com",
        core_business_summary="Travel editorial blog that wrote an article about medical tourism.",
        primary_services=["Travel blogging", "Ad content"],
        customer_types=["Readers"],
        target_category="Medical Tourism",
        business_relevance="INCIDENTAL",
        classification="MATCH",  # Simulated errant LLM output
        confidence=0.85,
        evidence_quality="LOW",
        supporting_evidence=[
            AIEvidenceItem(
                source_url="https://travelblogger.com/blog/medical-tourism-tips",
                page_title="Blog",
                page_type="BLOG",
                excerpt="Medical tourism is growing fast in 2026.",
                relevance="Mentions topic"
            )
        ],
        contradictory_evidence=[],
        reason="Mentions medical tourism in blog post.",
        review_required=False,
    )

    decision = QualificationDecisionEngine.evaluate(
        ai_resp=ai_resp,
        crawl_result=crawl_res,
        rule=get_sample_rule(),
        snov_result_raw="Qualified"
    )

    assert decision["final_classification"] == "NOT_A_MATCH"
    assert decision["business_relevance"] == "INCIDENTAL"
    assert decision["snov_verification"] == "CONTRADICTED"
    assert "Incidental mention" in decision["decision_reason"]


def test_inaccessible_website_becomes_unverifiable():
    """An inaccessible website must NEVER be auto-rejected as NOT_A_MATCH; it must be UNVERIFIABLE."""
    crawl_res = CrawlResult(
        domain="brokenurl.com",
        starting_url="https://brokenurl.com",
        status="FAILED",
        failure_reason="Connection timed out",
        pages=[]
    )

    decision = QualificationDecisionEngine.evaluate(
        ai_resp=None,
        crawl_result=crawl_res,
        rule=get_sample_rule(),
        snov_result_raw="Qualified"
    )

    assert decision["final_classification"] == "UNVERIFIABLE"
    assert decision["confidence"] == 0.0
    assert decision["snov_verification"] == "INCONCLUSIVE"


def test_hallucinated_citation_url_flags_review():
    """If AI invents a citation URL that was never fetched, flag for review."""
    crawl_res = CrawlResult(
        domain="exampleclinic.com",
        starting_url="https://exampleclinic.com",
        status="COMPLETED",
        pages=[
            FetchedPage(url="https://exampleclinic.com", page_type="HOMEPAGE", is_success=True),
        ]
    )

    ai_resp = AIClassificationResponse(
        company_name="Example Clinic",
        website_url="https://exampleclinic.com",
        core_business_summary="Clinic offering services.",
        primary_services=["Surgery"],
        customer_types=["Patients"],
        target_category="Medical Tourism",
        business_relevance="CORE",
        classification="MATCH",
        confidence=0.88,
        evidence_quality="HIGH",
        supporting_evidence=[
            AIEvidenceItem(
                source_url="https://exampleclinic.com/invented-secret-international-portal",  # NOT in crawl records!
                page_title="Invented",
                page_type="SERVICES",
                excerpt="We arrange everything.",
                relevance="Fake citation"
            )
        ],
        contradictory_evidence=[],
        reason="Claimed match.",
        review_required=False,
    )

    decision = QualificationDecisionEngine.evaluate(
        ai_resp=ai_resp,
        crawl_result=crawl_res,
        rule=get_sample_rule(),
        snov_result_raw="Qualified"
    )

    assert decision["final_classification"] == "NEEDS_REVIEW"
    assert len(decision["valid_supporting_evidence"]) == 0
    assert any("not present in fetched crawl records" in lim for lim in decision["limitations"])
