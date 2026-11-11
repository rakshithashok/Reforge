import pytest

from reforge.repair import _patch_paths


def test_patch_paths_rejects_test_and_escape_paths():
    with pytest.raises(ValueError, match="unsafe"):
        _patch_paths("--- a/a.py\n+++ b/../tests/test_x.py\n")
    assert _patch_paths("--- a/a.py\n+++ b/a.py\n")
