from app.services.risk_engine import RiskInputs, compute_repository_security_score, compute_vulnerability_risk, risk_band


def test_reachable_critical_scores_higher_than_unreachable_same_cvss():
    reachable = compute_vulnerability_risk(RiskInputs(
        cvss_score=9.8, exploit_available=True, reachable=True,
        is_production_dependency=True, is_direct=True, fix_available=True,
    ))[0]
    unreachable = compute_vulnerability_risk(RiskInputs(
        cvss_score=9.8, exploit_available=True, reachable=False,
        is_production_dependency=True, is_direct=True, fix_available=True,
    ))[0]
    assert reachable > unreachable


def test_explanation_mentions_cvss_and_reachability():
    score, explanation = compute_vulnerability_risk(RiskInputs(
        cvss_score=7.5, exploit_available=False, reachable=True,
        is_production_dependency=True, is_direct=True, fix_available=True,
    ))
    assert "7.5" in explanation
    assert "reachable" in explanation.lower()
    assert 0 <= score <= 100


def test_risk_band_thresholds():
    assert risk_band(10) == "LOW"
    assert risk_band(45) == "MEDIUM"
    assert risk_band(70) == "HIGH"
    assert risk_band(95) == "CRITICAL"


def test_repository_score_improves_when_risks_removed():
    before = compute_repository_security_score([90, 85, 70], reachable_critical_high=2)
    after = compute_repository_security_score([40], reachable_critical_high=0)
    assert after > before
