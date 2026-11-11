from reforge.analyze import analyze_project


def test_analysis_indexes_symbols_imports_and_calls(tmp_path):
    (tmp_path / "sample.py").write_text(
        "from sqlalchemy import select\n\ndef load():\n    return select(User)\n"
    )
    result = analyze_project(tmp_path)["sample.py"]
    assert result["symbols"][0]["qualified_name"] == "load"
    assert result["imports"][0]["module"] == "sqlalchemy"
    assert result["calls"][0]["callee"] == "select"
