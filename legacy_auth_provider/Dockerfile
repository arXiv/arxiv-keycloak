FROM python:3.12-slim
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends git build-essential gcc python3-dev default-libmysqlclient-dev pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/arxiv/
ENV VIRTUAL_ENV=/opt/arxiv/venv
RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ADD pyproject.toml poetry.lock src/legacy_auth_provider.py src/__init__.py src/user_model.py  src/logging.conf README.md ./

RUN $VIRTUAL_ENV/bin/pip install -U pip
RUN $VIRTUAL_ENV/bin/pip install poetry
# RUN $VIRTUAL_ENV/bin/poetry config virtualenvs.create false
RUN $VIRTUAL_ENV/bin/poetry lock
RUN $VIRTUAL_ENV/bin/poetry install --no-interaction --no-ansi
RUN $VIRTUAL_ENV/bin/pip uninstall -y poetry

ENV SQLALCHEMY_TRACK_MODIFICATIONS=False
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
CMD ["sh", "-c", "${VIRTUAL_ENV}/bin/uvicorn legacy_auth_provider:app --log-config=logging.conf --port=${PORT} --host=0.0.0.0"]
