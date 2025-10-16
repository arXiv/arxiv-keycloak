.PHONY: HELLO help up down
all: HELLO


HELLO:
	@echo To see the README of this Makefile, type "make help"

#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile


#-#
#-# up:
#-#   runs docker compose up with .env.
up: .env
	docker compose pull --quiet
	docker compose  -f /opt_arxiv/bomb-range/docker-compose.yaml up -d

#-#
#-# down:
#-#   runs docker compose down
down:
	docker compose  -f /opt_arxiv/bomb-range/docker-compose.yaml down
