
include ../.env
export $(shell sed 's/=.*//' ../.env)


app_tag := $(USER_PORTAL_APP_TAG)
app_name := $(USER_PORTAL_APP_NAME)
app_port := $(USER_PORTAL_APP_PORT)
dockerport := 8080

ROOT_DIR := $(shell pwd)

USER_PORTAL_APP_CPUS := $(shell echo $${USER_PORTAL_APP_CPUS:-2})
USER_PORTAL_APP_WORKERS := $(shell echo $${USER_PORTAL_APP_WORKERS:-2})

APP_DOCKER_RUN := docker run --cpus ${USER_PORTAL_APP_CPUS} --rm -p ${app_port}:${dockerport} \
-e PORT=${dockerport} -e WORKERS=${USER_PORTAL_APP_WORKERS} \
-e CLASSIC_DB_URI=${CLASSIC_DB_URI} \
-e SESSION_DURATION=36000 \
-e CLASSIC_COOKIE_NAME=tapir_session \
-e JWT_SECRET=${JWT_SECRET} \
--name ${app_name} --security-opt="no-new-privileges=true"

# -e DOMAIN=${DOMAIN} \


.PHONY: HELLO docker-image run stop

default: HELLO venv/lib/python3.11/site-packages/fastapi

HELLO:
	@echo To see the README of this Makefile, type "make help"
	@echo Local HTTP port is ${app_port}
	@echo Docker command params is:
	@echo ${APP_DOCKER_RUN}

bootstrap: venv/lib/python3.11/site-packages/fastapi

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


/usr/bin/python3.11:
	sudo apt install -y python3.11

/usr/lib/python3.11/ensurepip/__init__.py:
	sudo apt install -y python3.11-venv

.bootstrap:
	sudo apt install -y libmysqlclient-dev build-essential python3.11-dev
	touch .bootstrap

venv: /usr/bin/python3.11 /usr/lib/python3.11/ensurepip/__init__.py .bootstrap
	python3.11 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install --upgrade pip && pip install poetry

venv/lib/python3.11/site-packages/fastapi: venv/bin/poetry
	. venv/bin/activate && poetry install

/usr/bin/docker:
	sh ./install-docker.sh

show-env:
	sed -e 's/^/export /g' ../.env


