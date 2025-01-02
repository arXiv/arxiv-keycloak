
include ../.env
export $(shell sed 's/=.*//' ../.env)

tag := ${LEGACY_AUTH_DOCKER_TAG}
port := ${LEGACY_AUTH_PROVIDER_PORT}
mysql_port := ${LEGACY_AUTH_PROVIDER_PORT}

.PHONY: login docker-image push deploy run sh bootstrap

bootstrap:
	@echo "nothing to be done"

docker-image:
	docker build --progress=plain --platform=linux/amd64 -t ${tag}:latest .

push:
	docker push ${tag}:latest

deploy:
	gcloud run deploy legacy-auth-provider \
	  --project=arxiv-development \
	  --image=${tag}:latest \
	  --port=8080 \
	  --platform=managed \
	  --allow-unauthenticated \
	  --region=us-central1 \
	  --max-instances=1 \
	  --min-instances=1 \
	  --execution-environment=gen2 \
	  --cpu=1 \
	  --memory=1Gi \
	  --timeout=300 \
	  --concurrency=2 \
	  --set-env-vars SQLALCHEMY_RECORD_QUERIES=true \
	  --set-secrets=CLASSIC_DB_URI=browse-sqlalchemy-db-uri:latest,API_SECRET_KEY=jwt_secret:latest \
	  --session-affinity \
	  --set-cloudsql-instances arxiv-development:us-east4:arxiv-db-dev


run:
	docker run --rm -it --name legacy-auth-provider --network=host -e API_SECRET_KEY=secret -e PORT=${port} -e CLASSIC_DB_URI=mysql://dbuser:changeme@127.0.0.1:6201/arXiv ${tag}:latest

sh:
	docker run --rm -it --name legacy-auth-provider --network=host -e API_SECRET_KEY=secret PORT=${port} -e CLASSIC_DB_URI=mysql://dbuser:changeme@127.0.0.1:6201/arXiv --entrypoint=/bin/bash ${tag}:latest

login:
	gcloud auth login
	gcloud config set project arxiv-development
	gcloud auth configure-docker
