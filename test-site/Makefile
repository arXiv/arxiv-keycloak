include ../.env
export $(shell sed 's/=.*//' ../.env)

app_tag := "${TESTSITE_TAG}"

.PHONY: HELLO all load-test-data bootstrap run docker-image sh

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

venv: /usr/bin/python3.11
	python3.11 -m venv venv

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
	docker run --name testsite_app --rm -p ${TESTSITE_PORT}:${TESTSITE_PORT} -e JWT_SECRET=${JWT_SECRET} -e KC_URL_PUBLIC=${KC_URL_PUBLIC} -e KEYCLOAK_TEST_CLIENT_SECRET=${KEYCLOAK_TEST_CLIENT_SECRET} -e NGINX_PORT=${NGINX_PORT} -e PORT=${TESTSITE_PORT} ${app_tag}

sh:
	docker run --name testsite_app --rm -it -p ${TESTSITE_PORT}:${TESTSITE_PORT} -e JWT_SECRET=${JWT_SECRET} -e KC_URL_PUBLIC=${KC_URL_PUBLIC} -e KEYCLOAK_TEST_CLIENT_SECRET=${KEYCLOAK_TEST_CLIENT_SECRET} -e NGINX_PORT=${NGINX_PORT} -e PORT=${TESTSITE_PORT} ${app_tag} /bin/bash
