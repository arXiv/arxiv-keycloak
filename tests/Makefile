
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


#-#
#-# dump-arxiv-db:
#-#   dumps mysqldb://arxiv:arxiv_password@127.0.0.1:21504/arXiv?ssl=false&ssl_mode=DISABLED
dump-arxiv-db:
	mysqldump -n --user=root --password=root_password --host=127.0.0.1 --port=${ARXIV_DB_PORT} -q -y --skip-add-drop-table --skip-comments --skip-disable-keys --skip-lock-tables --ssl-mode=DISABLED --lock-all-tables --result-file ./data/test-db.sql arXiv

