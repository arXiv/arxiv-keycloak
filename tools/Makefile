include ../.env
export $(shell sed 's/=.*//' ../.env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all load-test-data bootstrap test upload-test-data dump-test-data lock update

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

.bootstrap: setup-$(OS)
	touch .bootstrap

setup-debian: .setup-debian

.setup-debian: venv/bin/poetry
	bash ./install_firefox_esr.sh
	touch .setup-debian

setup-arch: .setup-arch

.setup-arch:
	touch .setup-arch

venv:
	python3.12 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install poetry
	. venv/bin/activate && poetry lock && poetry install

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
#-# lock:
#-#   poretry lock 
lock: venv/bin/poetry
	. venv/bin/activate && poetry lock
	. venv/bin/activate && poetry install


#-#
#-# upload-test-data:
#-#   upload arxiv test db data
upload-test-data:
	gsutil cp /home/ntai/arxiv/arxiv-keycloak/tests/data/sanitized-test-db.sql gs://arxiv-dev-sql-data/test-data/arxiv-test-db.sql 

#-#
#-# dump-test-data:
#-#   dump arxiv test db data
dump-test-data:
	mysqldump -h 127.0.0.1 -P 21504 -u arxiv -parxiv_password --ssl-mode=DISABLED --result-file="/home/ntai/arxiv/arxiv-keycloak/tests/data/sanitized-test-db.sql" --complete-insert --skip-add-drop-table arXiv


#-#
#-# Command: update
#-#   run poetry update
update: venv/bin/poetry
	. venv/bin/activate && poetry update
