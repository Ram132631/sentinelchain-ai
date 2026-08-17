from app.sbom.sbom_generator import _parse_package_json, _parse_package_lock, _parse_requirements_txt


def test_parse_package_json_extracts_direct_deps():
    components = {}
    _parse_package_json('{"dependencies": {"lodash": "^4.17.19", "axios": "0.21.1"}}', components)
    assert components["npm:lodash"].version == "4.17.19"
    assert components["npm:lodash"].is_direct is True
    assert components["npm:axios"].version == "0.21.1"


def test_parse_requirements_txt_extracts_pinned_versions():
    components = {}
    _parse_requirements_txt("flask==2.0.1\n# a comment\nrequests>=2.25.0\n", components)
    assert components["pypi:flask"].version == "2.0.1"
    assert components["pypi:requests"].ecosystem == "PyPI"


def test_parse_package_lock_v2_marks_transitive_depth():
    lock = '{"lockfileVersion": 3, "packages": {"": {}, "node_modules/express": {"version": "4.17.1"}, "node_modules/express/node_modules/debug": {"version": "2.6.9"}}}'
    components = {}
    _parse_package_lock(lock, components)
    assert components["npm:express"].is_direct is True
    assert components["npm:debug"].is_direct is False
