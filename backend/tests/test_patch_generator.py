from app.patching.patch_generator import assess_breaking_change_risk, build_dependency_diff, parse_semver


def test_parse_semver():
    assert parse_semver("4.17.21") == (4, 17, 21)
    assert parse_semver("bogus") == (0, 0, 0)


def test_patch_bump_is_low_risk():
    risk, _ = assess_breaking_change_risk("4.17.19", "4.17.21")
    assert risk == "LOW"


def test_minor_bump_is_medium_risk():
    risk, _ = assess_breaking_change_risk("2.29.1", "2.30.1")
    assert risk == "MEDIUM"


def test_major_bump_is_high_risk():
    risk, _ = assess_breaking_change_risk("6.3.0", "7.5.2")
    assert risk == "HIGH"


def test_diff_shows_version_change():
    diff = build_dependency_diff("package.json", "lodash", "4.17.19", "4.17.21")
    assert '"lodash": "4.17.19"' in diff
    assert '"lodash": "4.17.21"' in diff
    assert diff.count("-") >= 1 and diff.count("+") >= 1
