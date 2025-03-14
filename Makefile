
DOCKER_DIRS := keycloak_bend oauth2-authenticator keycloak_tapir_bridge legacy_auth_provider test-mta user-portal account-ui
ALL_DIRS := $(DOCKER_DIRS) tools tests

include .env
export $(shell sed 's/=.*//' .env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all bootstrap docker-image arxiv-db nginx test up down restart images

default: HELLO


define run_in_docker_dirs
	@for dir in $(DOCKER_DIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef

define parallel_run_in_docker_dirs
	@echo "Building in parallel..."
endef


define run_in_all_subdirs
	@for dir in $(ALL_DIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef

HELLO:
	@echo First, run "bash config.sh" , if this is first time. It sets up the .env file.
	@echo To see the README of this Makefile, type "make help"
	@echo Then, "make bootstrap" to set up the environment.
	@echo "make docker-image" builds the docker images

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

.bootstrap: tests/data/sanitized-test-db.sql setup-$(OS)
	$(call run_in_all_subdirs,bootstrap)
	touch .bootstrap

setup-debian: .setup-debian

.setup-debian:
	sudo apt install -y libmysqlclient-dev build-essential python3.12-dev
	pyenv update && pyenv install -s 3.12
	$(call run_in_all_subdirs,bootstrap)
	touch .setup-debian

setup-arch: .setup-arch

.setup-arch:
	$(call run_in_all_subdirs,bootstrap)
	touch .setup-arch

#-#
#-# docker-image:
#-#   builds docker images
docker-image:
	$(call run_in_docker_dirs,docker-image)

images:
	@echo "Building docker images in parallel..."
	@echo "$(DOCKER_DIRS)" | tr ' ' '\n' | xargs -P 8 -I {} $(MAKE) -C {} docker-image

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
#-# up:
#-#   runs docker compose up with .env.
devup: .env
	docker compose -f ./docker-compose-devdb.yaml --env-file=.env.devdb up -d

#-#
#-# down:
#-#   runs docker compose down
devdown:
	docker compose -f ./docker-compose-devdb.yaml --env-file=.env.devdb down


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
#-# arxiv-test-db:
#-#   loads the arxiv-db aka mysql database.
#-#   NOTE: you need to run docker compose ("make up") so that the network exists.
arxiv-test-db:
	docker run --rm --name arxiv-db-setup \
	--network host \
	-e CLASSIC_DB_URI="mysql+pymysql://arxiv:arxiv_password@127.0.0.1:${ARXIV_DB_PORT}/arXiv?&ssl_disabled=true" \
	-v $(PWD):/arxiv-keycloak \
	python:3.12 bash /arxiv-keycloak/tools/load_test_data.sh

#-#
#-# restart:
#-#   restarts nginx (so that it picks up the new config)
restart:
	docker kill nginx-proxy
	docker start nginx-proxy


tests/data/sanitized-test-db.sql:
	gsutil cp gs://arxiv-dev-sql-data/test-data/sanitized-test-db.sql $@
#-#
