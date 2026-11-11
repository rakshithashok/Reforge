from reforge.audit import change_size, test_snapshot, tests_unchanged


def test_test_snapshot_detects_modified_test_file(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    target = tests / "test_sample.py"
    target.write_text("assert True\n")
    before = test_snapshot(tmp_path)
    target.write_text("assert False\n")
    assert not tests_unchanged(tmp_path, before)


def test_change_size_counts_replaced_lines_without_git():
    assert change_size("a\nb\n", "a\nc\nd\n") == 2
