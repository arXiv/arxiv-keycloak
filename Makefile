
DOCKER_DIRS := keycloak_bend oauth2-authenticator keycloak_tapir_bridge legacy_auth_provider
ALL_DIRS := $(DOCKER_DIRS) tools tests

include .env
export $(shell sed 's/=.*//' .env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all bootstrap docker-image start arxiv-db nginx test

all: HELLO


define run_in_docker_dirs
	@for dir in $(DOCKER_DIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef

define run_in_all_subdirs
	@for dir in $(ALL_DIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef

HELLO:
	@echo To see the README of this Makefile, type "make help"
	@echo First, run "bash config.sh"
	@echo Then, "make bootstrap" to set up the environment.

#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

.env: .env.localdb

.env.localdb:
	bash config.sh > /dev/null


#-#
#-# bootstrap:
#-#   bootstraps the environment
bootstrap: .bootstrap

.bootstrap:
	./tools/install_py311.sh
	$(call run_in_all_subdirs,bootstrap)
	touch .bootstrap

#-#
#-# docker-image:
#-#   builds docker images
docker-image:
	$(call run_in_docker_dirs,docker-image)

#-#
#-# up:
#-#   runs docker compose up with .env.
up: .env
	docker compose --env-file=.env up -d

#-#
#-# down:
#-#   runs docker compose down
down:
	docker compose --env-file=.env down


#-#
#-# test:
#-#   runs test in all of subdirectories
test:
	$(call run_in_all_subdirs,test)

#-#
#-# nginx:
#-#   runs nginx docker container and get into shell.
#-#   NOTE: you need to run docker compose ("make up") so that the network exists.
nginx:
	docker run -it --rm \
	--network arxiv-keycloak_arxiv-network \
	-v ./tests/config/nginx-docker.conf:/etc/nginx/nginx.conf \
	-p ${NGINX_PORT}:${NGINX_PORT} \
	nginx:latest /bin/bash


sh-nginx:
	docker exec -it nginx-proxy /bin/bash


#-#
#-# arxiv-db:
#-#   loads the arxiv-db aka mysql database.
#-#   NOTE: you need to run docker compose ("make up") so that the network exists.
arxiv-db:
	docker run --rm --name arxiv-db-setup \
	--network arxiv-keycloak_arxiv-network \
	-e CLASSIC_DB_URI="mysql://root:root_password@arxiv-test-db:${ARXIV_DB_PORT}/arXiv" \
	-v $(PWD):/arxiv-keycloak \
	python:3.11 bash /arxiv-keycloak/tools/load_test_data.sh

#-#
