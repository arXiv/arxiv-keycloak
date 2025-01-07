include ../.env
export $(shell sed 's/=.*//' ../.env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all load-test-data

all: ../venv/bin/poetry HELLO 

HELLO:
	@echo To see the README of this Makefile, type "make help"


../venv: /usr/bin/python3.11
	cd .. && ${MAKE} venv

../venv/bin/poetry: ../venv
	. ../venv/bin/activate && pip install poetry
	. ../venv/bin/activate && pip poetry

load-test-data: ../venv
	. ../venv/bin/activate && CLASSIC_DB_URI=${CLASSIC_DB_URI} python3 ./load_test_data.py
