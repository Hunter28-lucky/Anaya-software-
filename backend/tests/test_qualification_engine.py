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

    assert decision["final_classification"] == "NOT_A_MATCH"
    assert len(decision["valid_supporting_evidence"]) == 0
    assert any("not present in fetched crawl records" in lim for lim in decision["limitations"])


def test_strict_binary_confirmation_placidway_matches():
    """Proves PlacidWay content classifies as MATCH with high confidence and citations."""
    crawl_res = CrawlResult(
        domain="placidway.com",
        starting_url="https://www.placidway.com",
        status="COMPLETED",
        pages=[
            FetchedPage(
                url="https://www.placidway.com",
                page_type="HOMEPAGE",
                page_title="PlacidWay Medical Tourism | Affordable Surgery Overseas",
                clean_text="PlacidWay connects international patients with accredited hospitals worldwide for medical travel and surgery abroad.",
                is_success=True,
            )
        ]
    )

    decision = QualificationDecisionEngine.evaluate(
        ai_resp=None,  # Tests semantic content analyzer
        crawl_result=crawl_res,
        rule=get_sample_rule(),
        snov_result_raw="Health, Wellness & Fitness"
    )

    assert decision["final_classification"] == "MATCH"
    assert decision["final_classification"] != "NEEDS_REVIEW"
    assert decision["confidence"] >= 0.85
    assert len(decision["valid_supporting_evidence"]) > 0


def test_strict_binary_confirmation_qresorts_rejected():
    """Proves resort/hotel like qresorts.in is decisively classified as NOT_A_MATCH."""
    crawl_res = CrawlResult(
        domain="qresorts.in",
        starting_url="https://qresorts.in",
        status="COMPLETED",
        pages=[
            FetchedPage(
                url="https://qresorts.in",
                page_type="HOMEPAGE",
                page_title="Luxury Beach Resort & Convention Centre",
                clean_text="Welcome to our luxury beach resort. Suites & rooms, banquet hall, swimming pool, and dining.",
                is_success=True,
            )
        ]
    )

    decision = QualificationDecisionEngine.evaluate(
        ai_resp=None,
        crawl_result=crawl_res,
        rule=get_sample_rule(),
        snov_result_raw="Hospitality"
    )

    assert decision["final_classification"] == "NOT_A_MATCH"
    assert decision["final_classification"] != "NEEDS_REVIEW"
    assert "Hospitality" in decision["decision_reason"] or "hospitality" in decision["decision_reason"].lower()


def test_ambiguous_ai_response_enforced_to_binary():
    """Proves when AI attempts to return NEEDS_REVIEW, engine forces a decisive binary decision."""
    crawl_res = CrawlResult(
        domain="example.com",
        starting_url="https://example.com",
        status="COMPLETED",
        pages=[
            FetchedPage(
                url="https://example.com",
                page_type="HOMEPAGE",
                clean_text="General company offering miscellaneous services.",
                is_success=True,
            )
        ]
    )

    ai_resp = AIClassificationResponse(
        company_name="Ambiguous Co",
        website_url="https://example.com",
        core_business_summary="Some business",
        primary_services=[],
        customer_types=[],
        target_category="Medical Tourism",
        business_relevance="UNKNOWN",
        classification="NEEDS_REVIEW",  # Model attempted to return NEEDS_REVIEW!
        confidence=0.50,
        evidence_quality="LOW",
        supporting_evidence=[],
        contradictory_evidence=[],
        reason="Unclear",
        review_required=True,
    )

    decision = QualificationDecisionEngine.evaluate(
        ai_resp=ai_resp,
        crawl_result=crawl_res,
        rule=get_sample_rule(),
        snov_result_raw=None
    )

    # Must be decisively binary: NOT_A_MATCH (never NEEDS_REVIEW!)
    assert decision["final_classification"] in ("MATCH", "NOT_A_MATCH")
    assert decision["final_classification"] != "NEEDS_REVIEW"
    assert decision["final_classification"] == "NOT_A_MATCH"

