FROM reforge-sandbox:latest

USER root
RUN pip install --no-cache-dir \
    "SQLAlchemy>=1.4.53,<2.1" \
    "SQLAlchemy-Utils>=0.41.2" \
    "Flask>=0.9" \
    "Flask-Login>=0.2.9" \
    "Flask-SQLAlchemy>=1.0" \
    "SQLAlchemy-i18n>=0.8.4,!=1.1.0" \
    "PyMySQL>=0.8.0" \
    "psycopg2-binary>=2.9" \
    packaging
USER runner
