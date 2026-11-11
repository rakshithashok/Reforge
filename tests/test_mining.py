import subprocess

from training.mine_repos import mine


def _git(repository, *args):
    subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, text=True)


def test_mine_records_parent_and_migration_commit(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "Tests")
    target = repository / "models.py"
    target.write_text("session.query(User).get(user_id)\n")
    _git(repository, "add", "models.py")
    _git(repository, "commit", "-m", "use sqlalchemy legacy API")
    before = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"], capture_output=True,
                            text=True, check=True).stdout.strip()
    target.write_text("session.get(User, user_id)  # sqlalchemy 2.0\n")
    _git(repository, "add", "models.py")
    _git(repository, "commit", "-m", "migrate sqlalchemy 2.0")
    records = mine(repository, "MIT", ["python", "-m", "pytest"])
    assert len(records) == 1
    assert records[0]["commit"] == before
    assert records[0]["test_command"] == ["python", "-m", "pytest"]
