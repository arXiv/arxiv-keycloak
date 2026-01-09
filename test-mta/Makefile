include ../.env
export $(shell sed 's/=.*//' ../.env)

app_tag := "${TEST_MTA_TAG}"
app_name := "test-mta"

email_to_pubsub_app_tag := "${EMAIL_TO_PUBSUB_APP_TAG}"
email_to_pubsub_app_name := "email-to-pubsub-relay"

.PHONY: HELLO all bootstrap run docker-image sh relay relay.push update

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

setup-debian: venv/lib/python3.12/site-packages/fastapi

setup-arch:

venv:
	python3.12 -m venv venv


venv/lib/python3.12/site-packages/fastapi: venv
	. venv/bin/activate && pip install -r ./requirements.txt

#-#
#-# Command: docker-image
#-#   builds the docker image
docker-image:
	@echo "tag: ${app_tag}"
	docker buildx build -f ./Dockerfile \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t ${app_tag}:latest .
	@echo "tag: ${email_to_pubsub_app_tag}"
	docker buildx build -f ./email-to-pubsub.Dockerfile \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t ${email_to_pubsub_app_tag}:latest .

#-#
#-# Command: run
#-#   runs the docker image
run:
	docker run --name ${app_name} --rm     -p ${SMTP_PORT}:${SMTP_PORT} -p ${MAIL_API_PORT}:${MAIL_API_PORT} -e MAIL_API_PORT=${MAIL_API_PORT} -e SMTP_PORT=${SMTP_PORT} ${app_tag}

#-#
#-# Command: relay
#-#   runs the email relay docker image
relay:
	docker run --name ${email_to_pubsub_app_name} --rm -p ${SMTP_PORT}:${SMTP_PORT} -p ${MAIL_API_PORT}:${MAIL_API_PORT} -e MAIL_API_PORT=${MAIL_API_PORT} -e SMTP_PORT=${SMTP_PORT} ${email_to_pubsub_app_tag}

#-#
#-# Command: relay.push
#-#   runs the email relay docker image
relay.push:
	docker push  ${email_to_pubsub_app_tag}

#-#
#-# Command: lock
#-#   run poetry lock
lock:
	@echo "does not use poetry"


#-#
#-# Command: update
#-#   noop
lock:
	@echo "does not use poetry"

