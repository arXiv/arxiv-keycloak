
include ../.env
export $(shell sed 's/=.*//' ../.env)

TESTS_DIR ?= $(abspath $(CURDIR))


.PHONY: all bootstrap test HELLO help lock update 

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

# mysqldump -h 127.0.0.1 -u testuser -ptestpassword --no-create-info --skip-triggers --compact --single-transaction --ssl-mode=DISABLED arXiv arXiv_endorsements arXiv_endorsements_audit | sed 's/INSERT INTO/INSERT IGNORE INTO/g' | mysql -h 127.0.0.1 -P 21504  -u root -proot_password --ssl-mode=DISABLED --force arXiv

#-#
#-# dump-arxiv-db:
#-#   dumps mysqldb://arxiv:arxiv_password@127.0.0.1:21504/arXiv?ssl=false&ssl_mode=DISABLED
dump-arxiv-db:
	mysqldump -n --user=root --password=root_password --host=127.0.0.1 --port=${ARXIV_DB_PORT} -q -y --skip-add-drop-table --skip-comments --skip-disable-keys --skip-lock-tables --ssl-mode=DISABLED --lock-all-tables --result-file ./data/test-db.sql arXiv

#-#
#-# Command: lock
#-#   noop
lock:
	@echo Nothing to be done

#-#
#-# Command: update
#-#   noop
update:
	@echo Nothing to be done


mysql2sqlite-image: /usr/bin/docker
	docker buildx build -f ./Dockerfile.mysql2sqlite \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t mysql2sqlite:latest .

mysql2sqlite: GID := $(shell id -g)
mysql2sqlite: UID := $(shell id -u)


mysql2sqlite:
	docker run --rm --network=host \
		--user $(UID):$(GID) \
		-v $(TESTS_DIR)/data:/data \
		mysql2sqlite \
		-f /data/arxiv-sqlite.db -d arXiv -u arxiv --mysql-password arxiv_password -h $(ARXIV_DB_HOST) -P $(ARXIV_DB_PORT)
