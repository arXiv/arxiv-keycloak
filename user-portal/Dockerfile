FROM python:3.12-bookworm

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 0E98404D386FA1D9 6ED0E7B82643E131 F8D2585B8783D481 54404762BBB6E853 BDE6D2B9216EC7A8 ; exit 0

RUN apt-get update -y -o APT::Get::AllowUnauthenticated=true && \
    apt-get install -y --allow-unauthenticated --no-install-recommends build-essential gcc python3-dev default-libmysqlclient-dev pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup venv and put into use. https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV

# Every python thing after this is in the venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN $VIRTUAL_ENV/bin/python -m pip install -U pip && \
    $VIRTUAL_ENV/bin/pip install poetry  && \
    $VIRTUAL_ENV/bin/poetry config virtualenvs.create false ; exit 0

WORKDIR /opt/arxiv/
COPY poetry.lock app-logging.conf pyproject.toml ./
COPY ./arxiv_user_portal/ ./arxiv_user_portal/
     
RUN $VIRTUAL_ENV/bin/poetry lock
RUN $VIRTUAL_ENV/bin/poetry install --no-ansi && $VIRTUAL_ENV/bin/pip uninstall -y poetry

ENV WORKERS=2
ENV SQLALCHEMY_TRACK_MODIFICATIONS=False
EXPOSE $PORT
CMD  $VIRTUAL_ENV/bin/gunicorn --bind 0.0.0.0:$PORT --log-config /opt/arxiv/app-logging.conf --workers $WORKERS --chdir arxiv_user_portal arxiv_user_portal.app:app
