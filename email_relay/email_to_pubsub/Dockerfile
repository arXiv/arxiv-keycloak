FROM python:3.12-slim
WORKDIR /app

ENV SMTP_PORT=21508

COPY email_to_pubsub.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "email_to_pubsub.py"]
