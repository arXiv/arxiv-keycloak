include ../.env
export $(shell sed 's/=.*//' ../.env)

app_tag := "${TEST_MTA_TAG}"
app_name := "test-mta"

.PHONY: HELLO all bootstrap run docker-image sh

all: ../venv/bin/poetry HELLO 

HELLO:
	@echo To see the README of this Makefile, type "make help"

#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# bootstrap:
#-#   sets up the tools.
bootstrap: venv/bin/poetry
	touch .bootstrap

venv: /usr/bin/python3.12
	python3.12 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install poetry
	. venv/bin/activate && poetry install

#-#
#-# Command: docker-image
#-#   builds the docker image
docker-image:
	@echo "tag: ${app_tag}"
	docker buildx build -f ./Dockerfile \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t ${app_tag}:latest .

#-#
#-# Command: run
#-#   runs the docker image
run:
	docker run --name ${app_name} --rm     -p ${SMTP_PORT}:${SMTP_PORT} -p ${MAILSTORE_PORT}:${MAILSTORE_PORT} -e MAILSTORE_PORT=${MAILSTORE_PORT} -e SMTP_PORT=${SMTP_PORT} ${app_tag}
