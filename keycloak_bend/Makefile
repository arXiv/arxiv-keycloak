
include ../.env
export $(shell sed 's/=.*//' ../.env)

tag := ${KC_DOCKER_TAG}

.PHONY: bootstrap run proxy sql docker-image push deploy local arxiv-realm sh-arxiv-realm test

all: .env.localdb
	@echo KC_DB_HOST_PUBLIC: ${KC_DB_HOST_PUBLIC}  KC_DB_HOST_PRIVATE:  ${KC_DB_HOST_PRIVATE}  KC_DB_USER: ${KC_DB_USER} KC_DB_PASS: ${KC_DB_PASS}
	@echo KC_ADMIN_PASSWORD: ${KC_ADMIN_PASSWORD}
	@echo ARXIV_USER_SECRET: ${ARXIV_USER_SECRET}
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile


#-#
#-# bootstrap:
#-#   bootstraps the environment
bootstrap: .bootstrap

.bootstrap: ./cert/dev-authdb-client-cert.pem
	../tools/install_py312.sh
	if ! dpkg -l | grep -q docker-compose-plugin; then sudo apt install -y docker-compose-plugin; fi
	${MAKE} venv/bin/poetry
	touch .bootstrap

./cert/dev-authdb-client-cert.pem:
	cd ./cert/ && ${MAKE} 

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
docker-image: keycloak_migration/keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar pubsub-listener/keycloak-pubsub-listener/target/keycloak-to-pubsub-1.0.0.jar
	docker build --progress plain -t ${tag}:latest .

keycloak_migration/keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar:
	cd keycloak_migration && $(MAKE) keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar

pubsub-listener/keycloak-pubsub-listener/target/keycloak-to-pubsub-1.0.0.jar:
	cd pubsub-listener && $(MAKE) keycloak-pubsub-listener-main/target/keycloak-to-pubsub-1.0.0.jar

#-#
#-# proxy:
#-#  Starts proxy connection to dev auth db using port 3030
proxy:
	/usr/local/bin/cloud-sql-proxy --address 0.0.0.0 --port 3030 arxiv-development:us-central1:authdb > /dev/null 2>&1 &

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
	gcloud run deploy keycloak-service \
          --project arxiv-development \
	  --image=${tag}:latest \
	  --platform=managed \
	  --allow-unauthenticated \
	  --region=us-central1 \
	  --max-instances=1 \
	  --min-instances=1 \
	  --cpu=1 \
	  --memory=2Gi \
	  --timeout=300 \
	  --concurrency=80 \
	  --set-env-vars=DB_ADDR=${KC_DB_HOST_PRIVATE},PROXY_MODE=--proxy-headers=forwarded,KEYCLOAK_ADMIN=admin,BOOTSTRAP=no,LOG_OUTPUT_FORMAT=--log-console-output=json,GCP_PROJECT_ID=arxiv-development \
	  --set-secrets=/secrets/authdb-certs/db-certs-expand.sh=authdb-certs:latest,KC_DB_PASS=authdb-password:latest,KEYCLOAK_ADMIN_PASSWORD=keycloak-admin-password:latest,GCP_CREDENTIALS=keycloak-pubsub-event-sa:latest \
	  --cpu-boost \
	  --session-affinity \
	  --vpc-egress=private-ranges-only

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
	python:3.11 sh /tools/setup-arxiv-realm.sh

sh-arxiv-realm:
	docker run -it --rm \
	--network arxiv-keycloak_arxiv-network \
	-v $(PWD):/keycloak_bend \
	-e KC_PORT="${KC_PORT}" \
	-e KEYCLOAK_SERVER_URL="http://keycloak:${KC_PORT}" \
	-e KC_ADMIN_PASSWORD="${KC_ADMIN_PASSWORD}" \
	-e ARXIV_USER_SECRET="${KEYCLOAK_TEST_CLIENT_SECRET}" \
	-e LEGACY_AUTH_TOKEN="${LEGACY_AUTH_API_TOKEN}" \
	python:3.11 /bin/bash

local-arxiv-realm:
	@ echo python3 tools/setup_arxiv_realm.py --server ${KC_URL_PUBLIC} --admin-secret ${KC_ADMIN_PASSWORD} --arxiv-user-secret "${ARXIV_USER_SECRET}" --legacy-auth-token "${LEGACY_AUTH_API_TOKEN}"
	. venv/bin/activate && python3 tools/setup_arxiv_realm.py --server localhost:${KC_PORT} --admin-secret ${KC_ADMIN_PASSWORD} --arxiv-user-secret "${ARXIV_USER_SECRET}" --legacy-auth-token "${LEGACY_AUTH_API_TOKEN}"

#-#
