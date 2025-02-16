include ../../.env
export $(shell sed 's/=.*//' ../../.env)

app_tag := ${ACCOUNT_PORTAL_APP_TAG}
app_name := ${ACCOUNT_PORTAL_APP_NAME}
app_port := ${ACCOUNT_PORTAL_APP_PORT}
# This is hard coded in nginx
dockerport := 8888

ROOT_DIR := $(shell pwd)
WEBAPP_CPUS := 2
WEBAPP_DOCKER_PLATFORM := $(shell echo $${WEBAPP_DOCKER_PLATFORM:-linux/amd64})
# // where the auth server is running.
# export const authUrl = process.env.AAA_URL || 'http://127.0.0.1:5000/aaa';
# // where the backend is running
# export const backendUrl = process.env.ADMIN_API_BACKEND_URL || 'http://127.0.0.1:5000/api/v1'
# // and the UI is serving from
# export const appUrl = process.env.ADMIN_APP_ROOT || 'http://127.0.0.1:5000/';
RUN_HOST := http://localhost.arxiv.org
# RUN_HOST := http://localhost:5000

APP_DOCKER_RUN := docker run --cpus ${WEBAPP_CPUS} --rm -p ${app_port}:${dockerport} \
-e WORKERS=4 \
-e AAA_URL=${RUN_HOST}/aaa \
-e ADMIN_API_BACKEND_URL=${RUN_HOST}/admin-api/v1 \
-e ACOOUNT_UI_APP_ROOT=${RUN_HOST}/user/ \
--name ${app_name} --security-opt="no-new-privileges=true" 

.PHONY: HELLO docker run stop build bootstrap aaa-api

default: HELLO

HELLO:
	@echo To see the README of this Makefile, type "make help"
	@echo Local HTTP port is ${app_port}
	@echo Docker command params is:
	@echo ${APP_DOCKER_RUN}

#-#
#-# Command: help
#-#   show this message
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# Command: bootstrap
#-#   installs packages

boostsrap: .bootstrap

.bootstrap:
	npm install
	touch .bootstrap

#-#
#-# Command: docker-image
#-#   builds the docker image
docker-image:
	@echo "PLATFORM: ${PLATFORM}"
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
	${APP_DOCKER_RUN} -it --rm ${app_tag}:latest 

#-#
#-# Command: daemon
#-#   runs the appliance container as a daemon
daemon: stop
	${APP_DOCKER_RUN} -d --rm ${app_tag}:latest 

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
	${APP_DOCKER_RUN}  -it ${app_tag}:latest /bin/sh


#-#
#-# Command: build
#-#   runs the vite build
build:
	npm run build

#-#
#-# Command: local
#-#   builds the docker image
local:
	@echo "PLATFORM: ${PLATFORM}"
	@echo "dockerport: ${app_port}"
	@echo "tag: ${app_tag}"
	docker buildx build -f ./Dockerfile.local \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t ${app_tag}:latest .

#-#
#-# Command: aaa-api
#-#   builds the docker image
aaa-api:
	# cd account-app && npm install --save-dev openapi-typescript
	npx openapi-typescript http://localhost:5100/aaa/openapi.json -o src/types/aaa-api.ts
	npx openapi-typescript http://localhost:5100/up-api/openapi.json -o src/types/up-api.ts
