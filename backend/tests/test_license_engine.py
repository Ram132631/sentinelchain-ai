from app.services.license_engine import classify_license, evaluate_policy


def test_classify_permissive():
    assert classify_license("MIT") == "PERMISSIVE"
    assert classify_license("Apache-2.0") == "PERMISSIVE"


def test_classify_copyleft():
    assert classify_license("AGPL-3.0") == "COPYLEFT"
    assert classify_license("GPL-3.0") == "COPYLEFT"


def test_classify_unknown():
    assert classify_license("") == "UNKNOWN"
    assert classify_license("Unknown") == "UNKNOWN"


def test_permissive_only_policy_flags_copyleft():
    violation, explanation = evaluate_policy("some-lib", "AGPL-3.0", "permissive-only")
    assert violation is True
    assert "AGPL-3.0" in explanation


def test_permissive_only_policy_allows_mit():
    violation, _ = evaluate_policy("some-lib", "MIT", "permissive-only")
    assert violation is False
