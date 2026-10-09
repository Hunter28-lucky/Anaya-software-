from app.services.snov_verifier import evaluate_snov_agreement


def test_snov_agrees_positive():
    status, reason = evaluate_snov_agreement("Qualified", "MATCH", "CORE")
    assert status == "SUPPORTED"


def test_snov_agrees_negative():
    status, reason = evaluate_snov_agreement("Rejected", "NOT_A_MATCH", "INCIDENTAL")
    assert status == "SUPPORTED"


def test_snov_contradicted_by_blog():
    status, reason = evaluate_snov_agreement("Qualified Facilitator", "NOT_A_MATCH", "INCIDENTAL")
    assert status == "CONTRADICTED"
    assert "False positive in Snov" in reason


def test_snov_partially_supported():
    status, reason = evaluate_snov_agreement("Qualified", "PARTIAL_MATCH", "SECONDARY")
    assert status == "PARTIALLY_SUPPORTED"


def test_snov_missing():
    status, reason = evaluate_snov_agreement(None, "MATCH", "CORE")
    assert status == "INCONCLUSIVE"
