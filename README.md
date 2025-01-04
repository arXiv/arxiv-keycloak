# arxiv-keycloak
## Overview

- keycloak_bend 
- oauth2-authenticator
- legacy_auth_provider
- keycloak_tapir_bridge

## Keycloak backend (keycloak_bend)

All the ingredients to assemble Keycloak Docker. It starts from existing release
Keycloak Docker. Following is added to it.

### arXiv theme

The login and user portal shall look like part of arXiv and thus we need a custome
theme.

### REST user federation
A key piece to migrate existing users to Keycloak.

This is to retrieve and authenticate the existing Tapir users. When Keycloak sees
an unregistered user, it tries this API to authenticate user, and if it succeeds,
the user is automatically registered to Keycloak.

### GCP pub/sub emitter

Sends the audit events to pubsub queue. Keycloak to Tapir bridge uses this to 
sync the user info between Keycloak and Tapir tables.

## OAuth2 authenticator (oauth2-authenticator)

This is sometimes called Cookie Maker. This provides the oauth2 callback
endpoint.

When the handshake with Keycloak succeeds, this sets up Tapir, and CE cookie.

In deployment, it is suggested to reverse-proxied from /aaa. (authentication,
authorization and account.).

As we do not really use authorization as of now, it is not a close match but
if we are to support the finer grained authorization, this is a logical place. 

## Legacy Auth Provider

`Tapir users --> Legacy Auth Provider --> Keycloak`

This is the endpoint for Keycloak's User federation to access in order to retrieve
Tapir user authentication and authorization.

## Keycloak Tapir Bridge (keycloak_tapir_bridge)

`Tapir users <-- Keycloak Tapir Bridge <-- Keycloak`

This service subscribes to the audit events from Keycloak and updates the 
Tapir data. 
The audit events includes the user's demographic such as names, emails, URLs.


# Development

- Bootstrap
- Build Docker Images
- Run Dockers with docker compose

Before you start, you need 1password CLI. The config.sh gets a few values from
1P and populates the values in .env.localdb.

At the root (arxiv-keycloak) directory, `make bootstrap`. See .env below.

## .env

./config.sh creates the file, and symlink .env --> .env.localdb.

Once created, you may change the .env as needed but YMMV. Adding is fine but
be careful of removing entries.

This is used for building Docker images as well as running Docker containers.


## Building Container images

`make docker-image`

## Local running

`make up`

`make down`

### Anatomy of Docker Compose

- auth-db: PostgreSQL for Keycloak backend
- arxiv-db: MySQL for arXiv backend
- pubsub: GCP pubsub emulator
- keycloak; Keycloak container
- oauth2-authenticator: oauth2 callback endpoint
- legacy-auth-provider
- keycloak-tapir-bridge
- nginx: To tie up the web site to the callback endpoint
- keycloak-setup: Creates "arxiv" realm, "arxiv-user" client and Legacy Auth user federation
- arxiv-db-setup: Creates and populates arXiv+Tapir tables

