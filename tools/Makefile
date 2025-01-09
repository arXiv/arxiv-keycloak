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
bootstrap: venv/bin/poetry
	bash ./install_firefox_esr.sh
	touch .bootstrap


venv: /usr/bin/python3.11
	python3.11 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install poetry
	. venv/bin/activate && poetry install


#-#
#-# load-test-data:
#-#   loads test data to arxiv db
load-test-data: venv/bin/poetry
	. venv/bin/activate && CLASSIC_DB_URI=${CLASSIC_DB_URI} python3 ./load_test_data.py


#-#
#-# test:
#-#   runs tests
test:
	@echo "No tests in tools yet"
