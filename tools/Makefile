include ../.env
export $(shell sed 's/=.*//' ../.env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO 

all: venv/bin/poetry HELLO 

HELLO:
	@echo To see the README of this Makefile, type "make help"


venv: /usr/bin/python3.11 
	python3.11 -m venv venv
	. venv/bin/activate && pip install --upgrade pip

venv/bin/poetry: venv
	. venv/bin/activate && pip install poetry

