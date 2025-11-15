FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY setup-job/requirements.txt /app/requirements.txt

# Install required Python packages
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the setup scripts
COPY tools/setup_arxiv_realm.py /app/setup_arxiv_realm.py
COPY setup-job/setup_realm_job.py /app/setup_realm_job.py

# Run the setup job wrapper
ENTRYPOINT ["python", "/app/setup_realm_job.py"]
