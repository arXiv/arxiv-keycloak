include ../.env
export $(shell sed 's/=.*//' ../.env)

tag := ${KC_TAPIR_BRIDGE_DOCKER_TAG}

.PHONY: bootstrap docker-image lock update

bootstrap: .bootstrap

.bootstrap: setup-$(OS)
	touch $@

setup-debian: .setup-debian

.setup-debian: venv/lib/python3.12/site-packages/google
	touch .setup-debian

setup-arch: .setup-arch

.setup-arch:
	touch .setup-arch

venv:
	python3.12 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install --upgrade pip && pip install poetry

venv/lib/python3.12/site-packages/google: venv/bin/poetry poetry.lock
	. venv/bin/activate && poetry install

docker-image:
	docker build -t ${tag} .

#-#
#-# lock:
#-#   runs tests
lock: venv/bin/poetry
	. venv/bin/activate && poetry lock
	. venv/bin/activate && poetry install

#-#
#-# update:
#-#   runs poetry update
update: venv/bin/poetry
	. venv/bin/activate && poetry update

