
include ../.env
export $(shell sed 's/=.*//' ../.env)


.PHONY: all bootstrap test HELLO help

all: HELLO bootstrap

HELLO:
	@echo To see the README of this Makefile, type "make help"

#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile


bootstrap: development

development:
	git clone https://github.com/arXiv/arxiv-base.git
	cd arxiv-base && git switch develop && git checkout 83af5ee568c5710ca3df0f6f68e39f998a772fa8 && mv development ../
	rm -fr ./arxiv-base ./development/sqlacodegen/tests

#-#
#-# test:
#-#   runs tests. This uses ../tools python venv
test:
	. ../tools/venv/bin/activate && pytest
