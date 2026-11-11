from pathlib import Path

from reforge.rules.sqlalchemy import SQLAlchemy20Rule


def test_query_get_rule_rewrites_session_get():
    source = "user = session.query(User).get(user_id)\n"
    after, sites = SQLAlchemy20Rule().transform(Path("models.py"), source)
    assert after == "user = session.get(User, user_id)\n"
    assert sites and sites[0].rule_id == "SA20_QUERY_GET"


def test_rule_leaves_other_query_calls_untouched():
    source = "user = session.query(User).filter(User.id == user_id).first()\n"
    after, sites = SQLAlchemy20Rule().transform(Path("models.py"), source)
    assert after == source
    assert sites == []


def test_rule_rewrites_legacy_select_and_case_lists():
    source = "statement = select([User, Address])\nvalue = case([(active, 1)], else_=0)\n"
    after, sites = SQLAlchemy20Rule().transform(Path("models.py"), source)
    assert after == "statement = select(User, Address)\nvalue = case((active, 1), else_=0)\n"
    assert [site.rule_id for site in sites] == ["SA20_SELECT_LIST", "SA20_CASE_LIST"]
