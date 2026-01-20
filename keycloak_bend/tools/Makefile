include ../../.env
export $(shell sed 's/=.*//' ../../.env)

app_tag := gcr.io/arxiv-development/arxiv-keycloak/python-keycloak-admin
app_name := python-keycloak-admin

.PHONY: HELLO docker-image run stop update

default: HELLO 

HELLO:
	@echo To see the README of this Makefile, type "make help"

bootstrap: setup-$(OS)

setup-debian:

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
#-# Command: sh
#-#   runs a bash shell in the container to look inside of it
sh:
	${APP_DOCKER_RUN}  -v ${HOME}/Downloads:/home/worker/Downloads -w /home/worker -it ${app_tag}:latest  /bin/bash


.bootstrap:
	touch .bootstrap

update:
	@echo ""
