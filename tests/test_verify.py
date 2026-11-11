from reforge.verify import _COVERAGE_MARKER, _coverage, _script


def test_coverage_is_read_from_marked_container_output():
    output = f"tests passed\n{_COVERAGE_MARKER}\n{{\"totals\": {{\"percent_covered\": 87.5}}}}"
    assert _coverage(output) == 87.5


def test_coverage_script_runs_configured_command_before_exporting_json():
    script = _script(["coverage", "run", "-m", "pytest"], collect_coverage=True)
    assert "coverage run -m pytest" in script
    assert "coverage json" in script
