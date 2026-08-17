from app.reachability.reachability_analyzer import analyze_demo, analyze_heuristic


def test_analyze_demo_reachable_case():
    spec = {
        "reachable": True, "entry_point": "GET /api/x", "vulnerable_function": "f()",
        "call_path": ["a", "b"], "reach_explanation": "because reasons",
    }
    result = analyze_demo(spec)
    assert result["is_reachable"] is True
    assert result["confidence"] > 0
    assert result["call_path"] == ["a", "b"]


def test_heuristic_flags_reachable_when_import_and_route_share_a_file():
    source_files = {
        "routes/products.js": "const ejs = require('ejs');\napp.get('/products', (req, res) => { ejs.render(); });",
    }
    result = analyze_heuristic("ejs", source_files)
    assert result["is_reachable"] is True


def test_heuristic_not_reachable_when_only_imported_in_a_script():
    source_files = {
        "scripts/build.js": "const lodash = require('lodash');\nlodash.merge({}, {});",
    }
    result = analyze_heuristic("lodash", source_files)
    assert result["is_reachable"] is False


def test_heuristic_not_reachable_when_package_never_imported():
    result = analyze_heuristic("left-pad-utils", {"routes/index.js": "app.get('/', () => {});"})
    assert result["is_reachable"] is False
