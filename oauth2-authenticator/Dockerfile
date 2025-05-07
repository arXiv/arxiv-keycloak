FROM python:3.12-bookworm AS builder

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends build-essential gcc python3-dev default-libmysqlclient-dev pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup venv and put into use. https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV

# Every python thing after this is in the venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN $VIRTUAL_ENV/bin/python -m pip install -U pip
RUN $VIRTUAL_ENV/bin/pip install poetry==2.1.1
RUN $VIRTUAL_ENV/bin/poetry config virtualenvs.create false ; exit 0

WORKDIR /opt/arxiv/

COPY poetry.lock app-logging.conf hypercorn-config.toml pyproject.toml ./
RUN ls $VIRTUAL_ENV/bin
     
RUN $VIRTUAL_ENV/bin/poetry lock 
RUN $VIRTUAL_ENV/bin/poetry install --no-ansi
RUN $VIRTUAL_ENV/bin/pip install hypercorn
RUN $VIRTUAL_ENV/bin/pip uninstall -y poetry

# final image
FROM python:3.12-slim-bookworm AS final
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libmariadb3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /opt/arxiv/
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY app-logging.conf hypercorn-config.toml pyproject.toml ./
COPY ./arxiv_oauth2 /opt/arxiv/arxiv_oauth2

ENV WORKERS=8
ENV SQLALCHEMY_TRACK_MODIFICATIONS=False
EXPOSE $PORT
CMD  $VIRTUAL_ENV/bin/hypercorn --config hypercorn-config.toml --bind 0.0.0.0:$PORT --log-config app-logging.conf --workers $WORKERS "arxiv_oauth2.main:create_app()"
