
SUBDIRS = keycloak_bend oauth2-authenticator keycloak_tapir_bridge legacy_auth_provider

include .env
export $(shell sed 's/=.*//' .env)


.PHONY: all bootstrap docker start arxiv-db

all: .env.localdb bootstrap
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

.env.localdb:
	config.sh > /dev/null


define run_in_subdirs
	@for dir in $(SUBDIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef

#-#
#-# bootstrap:
#-#   bootstraps the environment
bootstrap: .bootstrap

.bootstrap:
	$(call run_in_subdirs,bootstrap)
	$(MAKE) -C tests bootstrap
	touch .bootstrap

#-#
#-# docker-image:
#-#   builds docker images
docker-image:
	$(call run_in_subdirs,docker-image)

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
	-e CLASSIC_DB_URI="mysql://root:root_password@arxiv-test-db:3306/arXiv" \
	-v $(PWD):/arxiv-keycloak \
	python:3.11 bash /arxiv-keycloak/tools/load_test_data.sh

#-#
