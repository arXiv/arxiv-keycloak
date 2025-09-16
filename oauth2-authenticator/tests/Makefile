
DOCKER_DIRS := 
ALL_DIRS := 

include test-env
export $(shell sed 's/=.*//' test-env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all bootstrap docker-image arxiv-db nginx test up down restart images clean sh

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
	@echo First, run "bash config.sh" , if this is first time. It sets up the test-env file.
	@echo To see the README of this Makefile, type "make help"
	@echo Then, "make bootstrap" to set up the environment.
	@echo "make docker-image" builds the docker images

#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# bootstrap:
#-#   bootstraps the environment
bootstrap: .bootstrap

.bootstrap: tests/data/sanitized-test-db.sql setup-$(OS)
	$(call run_in_all_subdirs,bootstrap)
	touch .bootstrap

setup-debian:
setup-arch:
setup-redhat:

#-#
#-# up:
#-#   runs docker compose up with test-env.
up: 
	docker compose --env-file=test-env up -d

#-#
#-# down:
#-#   runs docker compose down
down:
	docker compose --env-file=test-env down --remove-orphans


#-#
#-# mta-models:
#-#   gets
mta-models:
	datamodel-codegen --url http://localhost:${MAIL_API_PORT}/openapi.json --input-file-type openapi --output mta_models.py
	-rm -fr fast-api-client/ test_mta_client/
	openapi-python-client generate --url http://localhost:${MAIL_API_PORT}/openapi.json && mv fast-api-client/fast_api_client ./test_mta_client

#-#
#-# clean:
#-# 
clean:

#-#
#-# sh:
#-# 
sh:
	docker compose --env-file=test-env -f ./docker-compose-db-init.yaml up
	# docker run python:3.12-bookworm -it -d /bin/sh
