def load_user(session, user_id):
    return session.query(User).get(user_id)  # noqa: F821
