# MySQL connection settings
MYSQL_HOST ?= 127.0.0.1
SQL_FILE ?= tests/data/test-arxiv-db-data.sql.gz

# OS for setup target (debian, arch, redhat)
OS ?= debian

# Dump settings
MYDUMPER_THREADS ?= 10
DUMP_DIR = ./tests/data/arxiv

DOCKER_DIRS := keycloak_bend oauth2-authenticator keycloak_tapir_bridge legacy_auth_provider test-mta user-portal account-ui 
ALL_DIRS := $(DOCKER_DIRS) tools tests

include .env
export $(shell sed 's/=.*//' .env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all bootstrap docker-image arxiv-db nginx test up down restart images lock deploy-db deploy-pubsub deploy-keycloak deploy-lap setup-keycloak update

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

setup-redhat: .setup-redhat
	pyenv update && pyenv install -s 3.12
	$(call run_in_all_subdirs,bootstrap)
	touch .setup-redhat

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
	docker compose --ansi=never --env-file=.env up -d

#-#
#-# down:
#-#   runs docker compose down
down:
	docker compose --ansi=never --env-file=.env down --remove-orphans


#-#
#-# up:
#-#   runs docker compose up with .env.
devup: .env
	docker compose --ansi=never -f ./docker-compose-devdb.yaml --env-file=.env.devdb up -d

#-#
#-# down:
#-#   runs docker compose down
devdown:
	docker compose --ansi=never -f ./docker-compose-devdb.yaml --env-file=.env.devdb down


#-#
#-# test:
#-#   runs test in all of subdirectories
test:
	$(call run_in_all_subdirs,test)

#-#
#-# lock:
#-#   runs lock in all of subdirectories
lock:
	$(call run_in_all_subdirs,lock)


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
#-# deploy-db:
#-#   delpoy the kc's auth db
deploy-db:
	gh workflow run deploy-keycloak-db.yml --ref ntai/wombat-81-testing -f env=wombat-81-testing


#-#
#-# deploy-pubsub:
#-#   delpoy the kc's pubsub for audit events
deploy-pubsub:
	gh workflow run deploy-keycloak-audit-pubsub.yml --ref ntai/wombat-81-testing -f env=wombat-81-testing

#-#
#-# deploy-keycloak:
#-#   delpoy the keycloak
deploy-keycloak:
	gh workflow run deploy-keycloak-svc.yml --ref ntai/wombat-81-testing -f env=wombat-81-testing  -f image_tag=ntai-wombat-81-testing


#-#
#-# deploy-lap:
#-#   delpoy the lagacy auth provider
deploy-lap:
	gh workflow run deploy-legacy-auth-provider.yml --ref ntai/wombat-81-testing -f env=wombat-81-testing  -f image_tag=ntai-wombat-81-testing

#-#
#-# setup-keycloak:
#-#   delpoy the lagacy auth provider
setup-keycloak:
	gh workflow run deploy-keycloak-setup.yml --ref ntai/wombat-81-testing -f env=wombat-81-testing  -f image_tag=ntai-wombat-81-testing


.PHONY:db-load-sql

db-load-sql:
	zcat ${SQL_FILE} | mysql --host ${MYSQL_HOST} -P ${ARXIV_DB_PORT} -u arxiv -parxiv_password arXiv

#-#
#-# test-db-dump-binary:
#-#   
TEST_DB_DUMP_DIR = ./tests/data/test-db-dump
GID := $(shell id -g)
UID := $(shell id -u)

.PHONY: dump-test-database
dump-test-database:
	@mkdir -p $(TEST_DB_DUMP_DIR)
	@if [ -d "$(TEST_DB_DUMP_DIR)" ] && [ -n "$$(ls -A $(TEST_DB_DUMP_DIR))" ]; then \
		echo "Removing existing dump files..."; \
		rm -rf $(TEST_DB_DUMP_DIR)/*; \
	fi
	docker run --rm \
		--network host \
		-v $(PWD)/$(TEST_DB_DUMP_DIR):/backup \
		-u $(UID):$(GID) \
		mydumper/mydumper \
		mydumper \
		-h 127.0.0.1 \
		-P 21504 \
		-u root \
		-p root_password \
		-B arXiv \
		-o /backup \
		--threads 4 \
		--compress \
		--sync-thread-lock-mode NO_LOCK \
		--verbose 3
	@echo "Done! Dump created in $(TEST_DB_DUMP_DIR)"


#-#
#-# update:
#-#   
update:
	$(call run_in_all_subdirs,update)

#-#

