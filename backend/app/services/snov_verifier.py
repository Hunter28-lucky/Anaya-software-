from typing import Optional, Tuple


def evaluate_snov_agreement(
    snov_raw: Optional[str],
    final_classification: str,
    business_relevance: str,
) -> Tuple[str, str]:
    """
    Evaluates whether the independent classification agrees with, contradicts,
    or partially supports the existing Snov research result.

    Returns:
        (snov_verification_status, explanation)
        Status is one of: SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, INCONCLUSIVE
    """
    if not snov_raw or not str(snov_raw).strip():
        return "INCONCLUSIVE", "No existing Snov research result was provided for comparison."

    snov_clean = str(snov_raw).strip().lower()

    # Determine if Snov believed it was positive, negative, or neutral
    snov_is_positive = any(term in snov_clean for term in [
        "qualified", "match", "yes", "true", "facilitator", "provider", "agency", "travel agency", "medical tourism"
    ])
    snov_is_negative = any(term in snov_clean for term in [
        "not a match", "rejected", "no", "false", "disqualified", "irrelevant", "unrelated"
    ])

    if final_classification in ("UNVERIFIABLE", "NEEDS_REVIEW"):
        return "INCONCLUSIVE", f"Independent website evaluation status is {final_classification}, so Snov result cannot be confirmed."

    if final_classification == "MATCH":
        if snov_is_positive:
            return "SUPPORTED", "Independent website audit confirmed first-party business operations matching Snov's positive assessment."
        elif snov_is_negative:
            return "CONTRADICTED", "Snov marked company as disqualified, but first-party website evidence proves genuine active operations."
        else:
            return "SUPPORTED", "First-party website audit verified active operations."

    elif final_classification == "PARTIAL_MATCH":
        if snov_is_positive:
            return "PARTIALLY_SUPPORTED", "Snov marked as fully qualified, but evidence indicates the offering is secondary or limited in scope."
        else:
            return "PARTIALLY_SUPPORTED", "Company provides secondary or partner-based services in this domain."

    elif final_classification == "NOT_A_MATCH":
        if snov_is_positive:
            if business_relevance == "INCIDENTAL":
                return "CONTRADICTED", "False positive in Snov: company merely mentioned the topic in blog or editorial news without providing commercial services."
            else:
                return "CONTRADICTED", "Snov marked company as qualified, but independent website evaluation found no genuine target service offering."
        elif snov_is_negative:
            return "SUPPORTED", "Both Snov and independent website audit agree that the company does not qualify."
        else:
            return "CONTRADICTED", "Independent audit determined NOT_A_MATCH based on extracted business evidence."

    return "INCONCLUSIVE", "Insufficient evidence to determine agreement."
