include ../.env
export $(shell sed 's/=.*//' ../.env)

tag := ${KC_TAPIR_BRIDGE_DOCKER_TAG}

.PHONY: bootstrap docker-image

bootstrap: .bootstrap

.bootstrap: venv/lib/python3.11/site-packages/google
	touch $@

venv:
	/usr/bin/python3.11 -m venv venv

venv/bin/poetry: venv
	. venv/bin/activate && pip install --upgrade pip && pip install poetry

venv/lib/python3.11/site-packages/google: venv/bin/poetry poetry.lock
	. venv/bin/activate && poetry install

docker-image:
	docker build -t ${tag} .
