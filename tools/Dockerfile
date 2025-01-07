FROM python:3.11-bookworm

RUN apt-get install -y --allow-unauthenticated --no-install-recommends build-essential gcc python3-dev default-libmysqlclient-dev pkg-config
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN apt-get update -y -o APT::Get::AllowUnauthenticated=true && \
    apt-get install -y --allow-unauthenticated --no-install-recommends build-essential gcc python3-dev default-libmysqlclient-dev pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV

# Every python thing after this is in the venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN $VIRTUAL_ENV/bin/python -m pip install -U pip
RUN $VIRTUAL_ENV/bin/pip install poetry
RUN $VIRTUAL_ENV/bin/poetry config virtualenvs.create false ; exit 0

WORKDIR /opt/arxiv/

COPY poetry.lock pyproject.toml load_test_data.py /opt/arxiv/

RUN $VIRTUAL_ENV/bin/poetry lock --no-update ; exit 0
RUN $VIRTUAL_ENV/bin/poetry install --no-dev --no-interaction --no-ansi ; exit 0

CMD ["sh", "-c", "${VIRTUAL_ENV}/bin/hypercorn --config hypercorn-config.toml --bind 0.0.0.0:${PORT} --log-config app-logging.conf --workers ${WORKERS} 'arxiv_oauth2.main:create_app()'"]
