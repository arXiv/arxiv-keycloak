FROM python:3.12-slim
WORKDIR /app

ENV SMTP_PORT=21508
ENV MAIL_API_PORT=21512

COPY email_to_pubsub.py .
COPY smtp_sink.py .
COPY email-to-pubsub-equirements.txt .
RUN pip install --no-cache-dir -r email-to-pubsub-equirements.txt

# Install supervisord and set up the config
RUN apt-get update && apt-get install -y --no-install-recommends supervisor && apt-get clean
COPY email-to-pubsub-supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisord to run both processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
