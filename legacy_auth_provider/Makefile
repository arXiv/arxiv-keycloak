
include ../.env
export $(shell sed 's/=.*//' ../.env)

tag := ${LEGACY_AUTH_DOCKER_TAG}
port := ${LEGACY_AUTH_PORT}
mysql_port := ${ARXIV_DB_PORT}

.PHONY: help login docker-image push deploy run sh bootstrap kill

all: help venv/lib/python3.12/site-packages/fastapi

#-#
#-# Hwo to: Run legacy auth provider under debugger
#-#
#-#   You need to run the docker compose up. You do go up a dir level, and `make up` to bring up necessary
#-#   services, and then kill the legacy auth provider.
#-#
#-#
#-# Command: help
#-#   show this message
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# Command: kill
#-#   kills legacy-auth-provider docker (but not remove)
kill:
	docker kill legacy-auth-provider

venv:
	python3.12 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install --upgrade pip && pip install poetry

venv/lib/python3.12/site-packages/fastapi: venv/bin/poetry
	. venv/bin/activate && poetry install

venv/bin/pytest: venv/lib/python3.12/site-packages/fastapi

bootstrap: setup-$(OS)
	@echo "nothing to be done"

setup-debian: venv/lib/python3.12/site-packages/fastapi

setup-arch:

docker-image:
	docker build --progress=plain --platform=linux/amd64 -t ${tag}:latest .

push:
	docker push ${tag}:latest

deploy:
	gcloud run deploy legacy-auth-provider \
	  --project=arxiv-development \
	  --image=${tag}:latest \
	  --port=8080 \
	  --platform=managed \
	  --allow-unauthenticated \
	  --region=us-central1 \
	  --max-instances=1 \
	  --min-instances=1 \
	  --execution-environment=gen2 \
	  --cpu=1 \
	  --memory=1Gi \
	  --timeout=300 \
	  --concurrency=2 \
	  --set-env-vars SQLALCHEMY_RECORD_QUERIES=true \
	  --set-secrets=CLASSIC_DB_URI=browse-sqlalchemy-db-uri:latest,API_SECRET_KEY=jwt_secret:latest \
	  --session-affinity \
	  --set-cloudsql-instances arxiv-development:us-east4:arxiv-db-dev


run:
	docker run --rm -it --name legacy-auth-provider --network=host -e API_SECRET_KEY=${LEGACY_AUTH_API_TOKEN} -e PORT=${LEGACY_AUTH_PORT} -e CLASSIC_DB_URI=mysql://arxiv:arxiv_password@127.0.0.1:${ARXIV_DB_PORT}/arXiv ${tag}:latest

sh:
	docker run --rm -it --name legacy-auth-provider --network=host -e API_SECRET_KEY=${LEGACY_AUTH_API_TOKEN} PORT=${LEGACY_AUTH_PORT} -e CLASSIC_DB_URI=mysql://arxiv:arxiv_password@127.0.0.1:${ARXIV_DB_PORT}/arXiv --entrypoint=/bin/bash ${tag}:latest

login:
	gcloud auth login
	gcloud config set project arxiv-development
	gcloud auth configure-docker


#-#
#-# Command: test
#-#   runs pytest
test: venv/bin/pytest
	. venv/bin/activate && poetry run pytest


#-#
