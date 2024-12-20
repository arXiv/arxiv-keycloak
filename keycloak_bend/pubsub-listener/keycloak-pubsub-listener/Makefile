SHELL := /bin/bash

help: ## Show this help message.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[$$()% a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

remove-image: ## Remove image from docker
	docker rmi -f $$(docker images -q keycloak-with-event-listener) || true

package: ## Package project
	mvn clean package

up: ## Start docker-compose
	docker compose up -d

rm: ## Stop and remove docker-compose
	docker compose stop
	docker compose rm -f

package-and-start: rm remove-image package up ## Package, stop, remove and start docker-compose
