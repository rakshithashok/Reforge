FROM python:3.11-slim
RUN pip install --no-cache-dir pytest coverage "libcst>=1.1" "PyYAML>=6.0"
RUN useradd --create-home --uid 10001 runner
WORKDIR /workspace
USER runner
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "-m", "pytest"]
