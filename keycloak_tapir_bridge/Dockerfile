FROM python:3.12-slim
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends git build-essential gcc python3-dev default-libmysqlclient-dev pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/arxiv/
ENV VIRTUAL_ENV=/opt/arxiv/venv
RUN python3 -m venv $VIRTUAL_ENV
RUN $VIRTUAL_ENV/bin/pip install -U pip
RUN $VIRTUAL_ENV/bin/pip install poetry

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ADD pyproject.toml poetry.lock src/ README.md ./

RUN $VIRTUAL_ENV/bin/poetry config virtualenvs.create false
RUN $VIRTUAL_ENV/bin/poetry lock
RUN $VIRTUAL_ENV/bin/poetry install --no-ansi
RUN $VIRTUAL_ENV/bin/pip uninstall -y poetry

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# ENV CLASSIC_DB_URI="${CLASSIC_DB_URI}"
CMD ["python", "src/main.py"]
