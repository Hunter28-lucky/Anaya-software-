from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AIEvidenceItem(BaseModel):
    source_url: str = Field(description="Exact URL of the fetched page containing the evidence")
    page_title: Optional[str] = Field(default=None, description="Title of the page")
    page_type: Optional[str] = Field(default=None, description="Type: HOMEPAGE, ABOUT, SERVICES, CONTACT, BLOG, etc.")
    excerpt: str = Field(description="Direct verbatim or tightly summarized text quote demonstrating the finding")
    relevance: str = Field(description="Why this excerpt proves or disproves qualification")


class AIClassificationResponse(BaseModel):
    company_name: str
    website_url: str
    core_business_summary: str = Field(description="Accurate factual summary of what the company actually sells or does")
    primary_services: List[str] = Field(default_factory=list, description="Primary commercial services or products offered")
    customer_types: List[str] = Field(default_factory=list, description="Target customer types (e.g. international patients, B2B, general public)")
    target_category: str = Field(description="Target industry evaluated, e.g., 'Medical Tourism'")
    business_relevance: Literal["CORE", "SECONDARY", "INCIDENTAL", "UNKNOWN"] = Field(
        description="Whether the target offering is core, secondary, incidental/editorial, or unknown"
    )
    classification: Literal["MATCH", "PARTIAL_MATCH", "NOT_A_MATCH", "NEEDS_REVIEW", "UNVERIFIABLE"]
    snov_result: Optional[str] = Field(default=None, description="Original research result supplied")
    snov_verification: Literal["SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "INCONCLUSIVE"] = Field(
        default="INCONCLUSIVE",
        description="Cross-check agreement between original Snov result and verified evidence"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Estimated confidence between 0.0 and 1.0")
    evidence_quality: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="MEDIUM")
    supporting_evidence: List[AIEvidenceItem] = Field(default_factory=list)
    contradictory_evidence: List[AIEvidenceItem] = Field(default_factory=list)
    reason: str = Field(description="Concise rationale explaining the classification decision")
    review_required: bool = Field(default=False, description="Whether human review is recommended")
    limitations: List[str] = Field(default_factory=list, description="Any coverage gaps, inaccessible pages, or ambiguities")
