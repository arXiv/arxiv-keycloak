include ../.env
export $(shell sed 's/=.*//' ../.env)

tag := ${KC_DOCKER_TAG}

.PHONY: bootstrap run proxy sql docker-image push deploy local arxiv-realm sh-arxiv-realm test dev9-arxiv-realm local-arxiv-realm deploy2 kc-service

all: .env.localdb
	@echo KC_DB_HOST_PUBLIC: ${KC_DB_HOST_PUBLIC}  KC_DB_HOST_PRIVATE:  ${KC_DB_HOST_PRIVATE}  KC_DB_USER: ${KC_DB_USER} KC_DB_PASS: ${KC_DB_PASS}
	@echo KC_ADMIN_PASSWORD: ${KC_ADMIN_PASSWORD}
	@echo ARXIV_USER_SECRET: ${ARXIV_USER_SECRET}
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile


#-#
#-# bootstrap:
#-#   bootstraps the environment
bootstrap: .bootstrap

.bootstrap: ./cert/dev-authdb-client-cert.pem ./keycloak-cert/keycloak-self-signed.jks setup-$(OS)
	touch .bootstrap

setup-debian: .setup-debian

.setup-debian:
	pyenv update && pyenv install -s 3.12
	if ! dpkg -l | grep -q docker-compose-plugin; then sudo apt install -y docker-compose-plugin; fi
	${MAKE} venv/bin/poetry
	touch .setup-debian

setup-arch: .setup-arch

.setup-arch:
	touch .setup-arch

./cert/dev-authdb-client-cert.pem:
	cd ./cert/ && ${MAKE} 

./keycloak-cert/keycloak-self-signed.jks:
	cd ./keycloak-cert/ && ${MAKE} 

venv:
	python3.12 -m venv venv
	. venv/bin/activate && pip install --upgrade pip

venv/bin/poetry: venv
	. venv/bin/activate && pip install poetry

venv/lib/python3.12/site-packeages/keycloak: venv/bin/poetry
	. venv/bin/activate && poetry install

#-#
#-# test:
#-#  Runs pytest
test:
	. venv/bin/activate && poetry run pytest

#-#
#-# run: 
#-#   runs the Keycloak and local Postgres DB for KC's backend db
run: docker-image .bootstrap
	KC_DOCKER_TAG=${tag} GCP_PROJECT=${GCP_PROJECT} GCP_CRED=${GCP_CRED} docker compose up -d

#-#
#-# kill: 
#-#   stops the Keycloak and local Postgres DB
kill: 
	KC_DOCKER_TAG=${tag} GCP_PROJECT=${GCP_PROJECT} GCP_CRED=${GCP_CRED} docker compose down

#-#
#-# sh:
#-#   Starts the shell in the Keycloak docker
sh:
	docker run --rm -it ${LOCAL_KEYCLOAK} --entrypoint /bin/bash  ${tag}:latest

#-#
#-# docker-image:
#-#   builds docker image
docker-image: keycloak_migration/keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar pubsub-listener/keycloak-to-pubsub-jar-with-dependencies.jar
	docker build --progress plain -t ${tag}:latest .

keycloak_migration/keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar:
	cd keycloak_migration && $(MAKE) keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar

# keycloak-to-pubsub-1.0.0.jar
pubsub-listener/keycloak-to-pubsub-jar-with-dependencies.jar:
	cd pubsub-listener && $(MAKE)

#-#
#-# proxy:
#-#  Starts proxy connection to dev auth db using port 3030
proxy:
	cloud-sql-proxy --address 0.0.0.0 --port 3030 arxiv-development:us-central1:authdb > /dev/null 2>&1 &

#-#
#-# sql:
#-#  This connects to the auth-db on -dev
sql:
	psql "sslmode=verify-ca sslrootcert=${HOME}/.arxiv/dev-authdb/dev-authdb-server-ca.pem sslcert=${HOME}/.arxiv/dev-authdb/dev-authdb-client-cert.pem sslkey=${HOME}/.arxiv/dev-authdb/dev-authdb-client-key.pem hostaddr=$KC_DB_ADDR_PUBLIC port=5432 user=keycloak dbname=keycloak"

#-#
#-# push:
#-#   uploads the docker image to GCP -dev
push:
	docker push ${tag}:latest

#-#
#-# init:
#-#   runs the keycloak docker on GCT -dev with BOOTSTAP=yes.
#-#   This is a one-time operation to get the URL and IP address
init:
	gcloud run deploy keycloak-service --image ${tag}:latest --platform managed --allow-unauthenticated --memory=2Gi --min-instances=1 --max-instances=1 \
	  --region us-central1 --set-env-vars "DB_ADDR=${KC_DB_HOST_PRIVATE},KC_DB_PASS=PROXY_MODE=--proxy-headers=forwarded,KEYCLOAK_ADMIN=admin,BOOTSTRAP=yes,LOG_OUTPUT_FORMAT=--log-console-output=json,GCP_PROJECT_ID=arxiv-development" \
	  --set-secrets=/secrets/authdb-certs/db-certs-expand.sh=authdb-certs:latest,KC_DB_PASS=authdb-password:latest,KEYCLOAK_ADMIN_PASSWORD=keycloak-admin-password:latest,GCP_CREDENTIALS=keycloak-pubsub-event-sa:latest \

#-#
#-# deploy:
#-#   deploys the keycloak docker on GCT -dev
#-#   Using the TCP connectin rather than proxy (for now) that you need to know the Keycloak IP address
#-#   and white-list the IP address at Postgres firewall.
deploy:
	gcloud run deploy keycloak-service --image=${tag}:latest  --flags-file=./dev-deploy.yaml


#-#
#-# DO NOT USE - NOT COMPLETE
#-# deploy2:
#-#   deploys the keycloak docker on GCT -dev
#-#   Using the TCP connectin rather than proxy (for now) that you need to know the Keycloak IP address
#-#   and white-list the IP address at Postgres firewall.
#-# 
deploy2:
	gcloud run services replace kc-service.yaml --dry-run --project=arxiv-development --region=us-central1  --platform=managed
	gcloud run services replace kc-service.yaml --project=arxiv-development --region=us-central1  --platform=managed


kc-service:
	gcloud run services describe keycloak-service \
	  --region=us-central1 \
	  --format export > service.yaml

#-#
#-# arxiv-realm:
#-#   loads the arxiv realm.
#-#   docker-compose loads this so no need to use this explicitly. However when you need to locally run,
#-#   this is handy, esp. when you have some issues with DB connection within the docker-compose network.
arxiv-realm:
	docker run --rm --name keycloak-setup \
	--network arxiv-keycloak_arxiv-network \
	-v $(PWD):/keycloak_bend \
	-e KC_PORT="${KC_PORT}" \
	-e KEYCLOAK_SERVER_URL="http://keycloak:${KC_PORT}" \
	-e KC_ADMIN_PASSWORD="${KC_ADMIN_PASSWORD}" \
	-e ARXIV_USER_SECRET="${KEYCLOAK_TEST_CLIENT_SECRET}" \
	-e LEGACY_AUTH_TOKEN="${LEGACY_AUTH_API_TOKEN}" \
	python:3.12 sh /tools/setup-arxiv-realm.sh

sh-arxiv-realm:
	docker run -it --rm \
	--network arxiv-keycloak_arxiv-network \
	-v $(PWD):/keycloak_bend \
	-e KC_PORT="${KC_PORT}" \
	-e KEYCLOAK_SERVER_URL="http://keycloak:${KC_PORT}" \
	-e KC_ADMIN_PASSWORD="${KC_ADMIN_PASSWORD}" \
	-e ARXIV_USER_SECRET="${KEYCLOAK_TEST_CLIENT_SECRET}" \
	-e LEGACY_AUTH_TOKEN="${LEGACY_AUTH_API_TOKEN}" \
	python:3.12 /bin/bash

local-arxiv-realm:
	@ echo python3 tools/setup_arxiv_realm.py --server ${KC_URL_PUBLIC} --admin-secret ${KC_ADMIN_PASSWORD} --arxiv-user-secret "${KEYCLOAK_TEST_CLIENT_SECRET}" --legacy-auth-token "${LEGACY_AUTH_API_TOKEN}"
	. venv/bin/activate && python3 tools/setup_arxiv_realm.py --server ${KC_URL_PUBLIC} --admin-secret ${KC_ADMIN_PASSWORD} --arxiv-user-secret "${KEYCLOAK_TEST_CLIENT_SECRET}" --legacy-auth-token "${LEGACY_AUTH_API_TOKEN}"

#-#

dev9-arxiv-realm:
	@echo python3 tools/setup_arxiv_realm.py --server https://keycloak-service-874717964009.us-central1.run.app  --admin-secret ${KC_ADMIN_PASSWORD} --arxiv-user-secret "${KEYCLOAK_TEST_CLIENT_SECRET}" --legacy-auth-token "${LEGACY_AUTH_API_TOKEN}"
	. venv/bin/activate && python3 tools/setup_arxiv_realm.py --server https://keycloak-service-874717964009.us-central1.run.app --admin-secret ${KC_ADMIN_PASSWORD} --arxiv-user-secret "${KEYCLOAK_TEST_CLIENT_SECRET}" --legacy-auth-token "${LEGACY_AUTH_API_TOKEN}" --source realms/arxiv-realm-gcp-dev.json
