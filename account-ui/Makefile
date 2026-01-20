
DOCKER_DIRS := account-app
ALL_DIRS := $(DOCKER_DIRS)

include ../.env
export $(shell sed 's/=.*//' ../.env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all bootstrap docker-image help lock update

default: HELLO

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
#-#   noop
bootstrap: .bootstrap

.bootstrap:
	$(call run_in_all_subdirs,bootstrap)
	touch .bootstrap

#-#
#-# Command: docker-image
#-#   builds the docker image
docker-image:
	$(call run_in_docker_dirs,docker-image)

lock:
	echo not a python project

update:
	$(call run_in_all_subdirs,update)
