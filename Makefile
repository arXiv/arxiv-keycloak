
SUBDIRS = keycloak_bend oauth2-authenticator keycloak_tapir_bridge legacy_auth_provider

include .env
export $(shell sed 's/=.*//' .env)


.PHONY: bootstrap docker start

all: .env.localdb bootstrap

.env.localdb:
	config.sh > /dev/null


define run_in_subdirs
	@for dir in $(SUBDIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef


bootstrap:
	$(call run_in_subdirs,bootstrap)

docker-image:
	$(call run_in_subdirs,docker-image)

up:
	docker compose --env-file=.env up -d

down:
	docker compose --env-file=.env down
