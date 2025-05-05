FROM python:3.12-bookworm
# Setup venv and put into use. https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV

# Every python thing after this is in the venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN $VIRTUAL_ENV/bin/python -m pip install -U pip
RUN $VIRTUAL_ENV/bin/pip install python-keycloak requests

CMD ["python"]
