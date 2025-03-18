
include ../.env
export $(shell sed 's/=.*//' ../.env)


.PHONY: HELLO

default: HELLO venv/lib/python3.12/site-packages/sqlalchemy

HELLO:
	@echo To see the README of this Makefile, type "make help"
	@echo Local HTTP port is ${app_port}
	@echo Docker command params is:
	@echo ${APP_DOCKER_RUN}

bootstrap: setup-$(OS)

setup-debian: venv/lib/python3.12/site-packages/sqlalchemy

setup-arch:

#-#
#-# Command: help
#-#   show this message
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# Command: docker-image
#-#   builds the docker image
docker-image:
	@echo "dockerport: ${app_port}"
	@echo "tag: ${app_tag}"
	docker buildx build -f ./Dockerfile \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t ${app_tag}:latest .

.bootstrap:
	touch .bootstrap

venv: .bootstrap
	python3.12 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install --upgrade pip && pip install poetry

venv/lib/python3.12/site-packages/sqlalchemy: venv/bin/poetry
	. venv/bin/activate && poetry install

