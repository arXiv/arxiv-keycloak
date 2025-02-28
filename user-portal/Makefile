
include ../.env
export $(shell sed 's/=.*//' ../.env)


app_tag := $(ARXIV_PORTAL_APP_TAG)
app_name := $(ARXIV_PORTAL_APP_NAME)
# app_port := $(ARXIV_PORTAL_APP_PORT)
app_port := $(ARXIV_PORTAL_PORT)
dockerport := 8080

ROOT_DIR := $(shell pwd)

ARXIV_PORTAL_APP_CPUS := $(shell echo $${ARXIV_PORTAL_APP_CPUS:-2})
ARXIV_PORTAL_APP_WORKERS := $(shell echo $${ARXIV_PORTAL_APP_WORKERS:-2})

APP_DOCKER_RUN := docker run --cpus ${ARXIV_PORTAL_APP_CPUS} --rm -p ${app_port}:${dockerport} \
-e PORT=${dockerport} -e WORKERS=${ARXIV_PORTAL_APP_WORKERS} \
-e CLASSIC_DB_URI="${CLASSIC_DB_URI}" \
-e SESSION_DURATION=36000 \
-e CLASSIC_COOKIE_NAME=tapir_session \
-e JWT_SECRET=${JWT_SECRET} \
-e AAA_TOKEN_REFRESH_URL=/aaa/refresh \
-e ARXIV_AUTH_DEBUG=True \
-e DEFAULT_LOGIN_REDIRECT_URL=/user-account/ \
-e DEFAULT_LOGOUT_REDIRECT_URL=/ \
--name ${app_name} --security-opt="no-new-privileges=true"

# -e DOMAIN=${DOMAIN} \


.PHONY: HELLO docker-image run stop

default: HELLO venv/lib/python3.12/site-packages/fastapi

HELLO:
	@echo To see the README of this Makefile, type "make help"
	@echo Local HTTP port is ${app_port}
	@echo Docker command params is:
	@echo ${APP_DOCKER_RUN}

bootstrap: setup-$(OS)

setup-debian: venv/lib/python3.12/site-packages/fastapi

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

#-#
#-# Command: run
#-#   runs the appliance container with the terminal attached (for test)
run: stop
	${APP_DOCKER_RUN} -it ${app_tag}:latest

#-#
#-# Command: stop
#-#   stops the appliance container
stop:
	-docker container kill ${app_name}
	-docker container rm ${app_name}

#-#
#-# Command: sh
#-#   runs a bash shell in the container to look inside of it
sh: stop
	${APP_DOCKER_RUN}  -v ${HOME}/Downloads:/home/worker/Downloads -w /home/worker -it ${app_tag}:latest  /bin/bash

#-#
#-# Command: daemon
#-#   runs the appliance container with the terminal attached (for test)
daemon: stop
	${APP_DOCKER_RUN} -d ${app_tag}:latest

.bootstrap:
	touch .bootstrap

venv: .bootstrap
	python3.12 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install --upgrade pip && pip install poetry

venv/lib/python3.12/site-packages/fastapi: venv/bin/poetry
	. venv/bin/activate && poetry install

show-env:
	sed -e 's/^/export /g' ../.env


