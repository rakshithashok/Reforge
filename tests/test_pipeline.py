
from reforge.pipeline import migrate, migrate_verified
from reforge.types import VerificationResult


def test_pipeline_finds_rule_sites_without_mutating_by_default(tmp_path):
    (tmp_path / "models.py").write_text("result = session.query(User).get(key)\n")
    report = migrate(tmp_path, apply=False)
    assert len(report.changes) == 1
    assert (tmp_path / "models.py").read_text() == "result = session.query(User).get(key)\n"


def test_pipeline_never_rewrites_test_files(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    target = tests / "test_legacy.py"
    source = "result = session.query(User).get(key)\n"
    target.write_text(source)
    report = migrate(tmp_path, apply=True)
    assert report.changes == []
    assert target.read_text() == source


def test_verified_migration_reverts_when_candidate_fails(tmp_path, monkeypatch):
    target = tmp_path / "models.py"
    target.write_text("result = session.query(User).get(key)\n")
    results = iter([
        VerificationResult(True, 0, "", 0.0, 100.0),
        VerificationResult(False, 1, "failure", 0.0, 100.0),
    ])
    monkeypatch.setattr("reforge.pipeline.verify", lambda *args, **kwargs: next(results))
    report = migrate_verified(tmp_path, {"repair": {"minimal_diff_ratio": 4.0}})
    assert "Migrated repository verification failed" in report.human_review
    assert target.read_text() == "result = session.query(User).get(key)\n"
