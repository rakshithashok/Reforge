def load_user(session, user_id):
    return session.get(User, user_id)  # noqa: F821
