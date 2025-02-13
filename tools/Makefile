include ../.env
export $(shell sed 's/=.*//' ../.env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all load-test-data bootstrap test

all: ../venv/bin/poetry HELLO 

HELLO:
	@echo To see the README of this Makefile, type "make help"

#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

#-#
#-# bootstrap:
#-#   sets up the tools.
bootstrap: .bootstrap
	bash ./install_firefox_esr.sh
	touch .bootstrap

venv: /usr/bin/python3.11
	python3.11 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install poetry
	. venv/bin/activate && poetry install

.bootstrap: venv/bin/poetry
	touch .bootstrap

#-#
#-# load-arxiv-test-db-schema:
#-#   load the database shcema
load-schema: .bootstrap
	. venv/bin/activate && CLASSIC_DB_URI=${CLASSIC_DB_URI} python3 ./load_test_data.py


#-#
#-# load-test-data:
#-#   loads test data to arxiv db
load-test-data: .bootstrap
	. venv/bin/activate && CLASSIC_DB_URI=${CLASSIC_DB_URI} python3 ./load_test_data.py  --load-test-data


#-#
#-# test:
#-#   runs tests
test:
	@echo "No tests in tools yet"


#-#
#-# dump-test-data:
#-#   dump arxiv test db data
dump-test-data:
	mysqldump -h 127.0.0.1 -P 21504 -u arxiv -parxiv_password --ssl-mode=DISABLED --result-file="/home/ntai/arxiv/arxiv-keycloak/tests/data/sanitized-test-db.sql" --complete-insert --skip-add-drop-table arXiv

