#!/bin/bash

ACCOUNT=arxiv.1password.com


if [ ! -r .env.localdb ] ; then
    SERVER_HOST=localhost.arxiv.org
    PLATFORM=linux/amd64
    GCP_PROJECT=arxiv-development
    PUBSUB_PROJECT=local-test

    echo PUBSUB_PROJECT=$PUBSUB_PROJECT  >> .env.localdb
    echo DOCKER_NETWORK=arxiv-network >> .env.localdb

    # IRL, this is a secure "password" for encrypting JWT token
    JWT_SECRET=jwt-secret
    echo JWT_SECRET=$JWT_SECRET >> .env.localdb

    # IRL, this is a secure "password" for encrypting tapir cookie
    CLASSIC_SESSION_HASH=classic-secret
    echo CLASSIC_SESSION_HASH=$CLASSIC_SESSION_HASH >> .env.localdb
    
    echo DOCKER_PLATFORM=$PLATFORM >> .env.localdb
    
    # This is what nginx runs
    HTTP_PORT=5100
    echo NGINX_PORT=$HTTP_PORT >> .env.localdb

    # keycloak and its database
    KC_PORT=21501
    KC_HOST_PUBLIC=$SERVER_HOST

    # would be "keycloak" if the network is NOT host network
    KC_HOST_PRIVATE=localhost

    echo KC_PORT=$KC_PORT >> .env.localdb
    echo KC_HOST_PUBLIC=$KC_HOST_PUBLIC >> .env.localdb
    echo KC_HOST_PRIVATE=$KC_HOST_PRIVATE >> .env.localdb
    echo KC_URL_PUBLIC=http://$KC_HOST_PUBLIC:$KC_PORT >> .env.localdb
    echo KC_URL_PRIVATE=http://$KC_HOST_PRIVATE:$KC_PORT >> .env.localdb

    echo KC_DOCKER_TAG=gcr.io/$GCP_PROJECT/arxiv-keycloak/keycloak >> .env.localdb
    # kc db
    echo KC_DB_HOST_PUBLIC=$SERVER_HOST.arxiv.org >> .env.localdb
    echo KC_DB_HOST_PRIVATE=auth-db >> .env.localdb
    echo KC_DB_PORT=21502 >> .env.localdb
    echo KC_DB_USER=keycloak >> .env.localdb
    echo KC_DB_PASS=$(op item get  wos2wdt56jx2gjmvb4awlxk3ay --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "vlf6422dpbnqhne535fpgg4vqm") | .value') >> .env.localdb
    echo KC_ADMIN_PASSWORD=$(op item get  bdmmxlepkfsqy5hfgfunpsli2i --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "password") | .value') >> .env.localdb
    echo GCP_PROJECT=$PUBSUB_PROJECT >> .env.localdb
    echo KC_JDBC_CONNECTION="?ssl=false&sslmode=disable" >> .env.localdb
    echo GCP_CRED= >> .env.localdb
    # echo ARXIV_USER_SECRET=$(op item get  bdmmxlepkfsqy5hfgfunpsli2i --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "gxogpm2ztuyfeyvzjrwx4gqogi") | .value') >> .env.localdb
    # audit logging to GCP subsub
    # keycloak-tapir bridge uses this to update the tapir tables
    echo GCP_EVENT_TOPIC_ID=keycloak-arxiv-events >> .env.localdb
    echo GCP_ADMIN_EVENT_TOPIC_ID=keycloak-arxiv-events >> .env.localdb
    #
    # This is the oauth2 handshake (simple http auth secret)
    # Don't use this anywhere else since this is in github. Just for testing
    # This needs to be set to Keycloak's client.
    echo KEYCLOAK_TEST_CLIENT_SECRET=f3dc975132f09b27d90 >> .env.localdb
    #
    # oauth2 client - aka cookie maker
    #
    AAA_PORT=21503
    echo ARXIV_OAUTH2_CLIENT_TAG=gcr.io/$GCP_PROJECT/arxiv-keycloak/arxiv-oauth2-client >> .env.localdb
    echo ARXIV_OAUTH2_CLIENT_APP_NAME= arxiv-oauth2-client >> .env.localdb
    echo ARXIV_OAUTH2_APP_PORT=$AAA_PORT >> .env.localdb
    #
    # where aaa is hosted
    #
    echo AAA_CALLBACK_URL=http://$SERVER_HOST:$HTTP_PORT/aaa/callback >> .env.localdb
    echo AAA_LOGIN_REDIRECT_URL=http://$SERVER_HOST:$HTTP_PORT/aaa/login >> .env.localdb
    #
    # arxiv mysql db
    #
    # if you are using non-host docker network, this would be "arxiv-db" to match the container name
    # Do not use "localhost". It is special cased to use the Unix socket
    ARXIV_DB_HOST=127.0.0.1
    ARXIV_DB_PORT=21504
    echo ARXIV_DB_HOST=${ARXIV_DB_HOST} >> .env.localdb
    echo ARXIV_DB_PORT=${ARXIV_DB_PORT} >> .env.localdb
    echo CLASSIC_DB_URI="mysql+mysqldb://arxiv:arxiv_password@${ARXIV_DB_HOST}:${ARXIV_DB_PORT}/arXiv?ssl=false&ssl_mode=DISABLED"  >> .env.localdb
    #
    # legacy auth provider
    #
    LEGACY_AUTH_PORT=21505
    echo LEGACY_AUTH_PORT=${LEGACY_AUTH_PORT} >> .env.localdb
    # This is the dev-token but for local, use something else
    # echo LEGACY_AUTH_API_TOKEN=$(op item get  bdmmxlepkfsqy5hfgfunpsli2i --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "rs25xevxhbvy6l2aom7z633rti") | .value') >> .env.localdb
    echo LEGACY_AUTH_API_TOKEN=legacy-api-token >> .env.localdb
    echo LEGACY_AUTH_DOCKER_TAG=gcr.io/$GCP_PROJECT/arxiv-keycloak/legacy-auth-provider >> .env.localdb
    #
    #
    echo USER_PORTAL_APP_PORT=21506 >> .env.localdb
    echo USER_PORTAL_APP_TAG=gcr.io/arxiv-development/arxiv-keycloak/uesr-portal >> .env.localdb
    echo USER_PORTAL_APP_NAME=arxiv-user-portal >> .env.localdb
    #
    # pubsub emulator port
    #
    PUBSUB_PORT=21507
    # You'd need to define
    echo PUBSUB_EMULATOR_PORT=${PUBSUB_PORT} >> .env.localdb
    echo PUBSUB_EMULATOR_HOST=0.0.0.0:${PUBSUB_PORT} >> .env.localdb
    # See https://cloud.google.com/pubsub/docs/emulator
    #
    # Keycloak to tapir birdge
    echo KC_TAPIR_BRIDGE_DOCKER_TAG=gcr.io/$GCP_PROJECT/arxiv-keycloak/kc-tapir-bridge >> .env.localdb
    # keycloak-arxiv-events-sub is the default so you don't need for the python code but this is used to create
    # for subscription during the pubsub setup.
    # see GCP_EVENT_TOPIC_ID, GCP_ADMIN_EVENT_TOPIC_ID
    echo KC_TAPIR_BRIDGE_SUBSCRIPTION=keycloak-arxiv-events-sub >> .env.localdb
    #
    # email
    #
    SMTP_PORT=21508
    echo SMTP_PORT=$SMTP_PORT >> .env.localdb
    echo SMTP_HOST=0.0.0.0:$SMTP_PORT >> .env.localdb
    echo MAILSTORE_PORT=21512 >> .env.localdb
    echo TEST_MTA_TAG=gcr.io/$GCP_PROJECT/arxiv-keycloak/test-mta >> .env.localdb
    #
    #
    echo TESTSITE_TAG=gcr.io/$GCP_PROJECT/arxiv-keycloak/testsite >> .env.localdb
    echo TESTSITE_PORT=21509 >> .env.localdb
    #
    # This is not strictry necessary but here
    #
    echo ADMIN_API_PORT=21510 >> .env.localdb
    echo ADMIN_API_URL=http://$SERVER_HOST:$HTTP_PORT/admin-api >> .env.localdb
    echo ADMIN_CONSOLE_PORT=21511 >> .env.localdb
    echo ADMIN_CONSOLE_URL=http://$SERVER_HOST:$HTTP_PORT/admin-console >> .env.localdb
    #
    # portals
    #
    echo ARXIV_PORTAL_PORT=21513  >> .env.localdb
    echo USER_PORTAL_PORT=21514  >> .env.localdb
    #
    echo USER_PORTAL_API_PORT=21515 >>  .env.localdb
    echo USER_PORTAL_APP_NAME=arxiv-user-portal  >>  .env.localdb
    echo USER_PORTAL_APP_PORT=21506 >>  .env.localdb
    echo USER_PORTAL_APP_TAG=gcr.io/arxiv-development/arxiv-keycloak/uesr-portal  >>  .env.localdb
fi

if [ ! -r .env.devdb ] ; then
    echo KC_DOCKER_TAG=gcr.io/$GCP_PROJECT/arxiv-keycloak/keycloak >> .env.devdb
    echo KC_DB_HOST_PUBLIC=$(op item get  wos2wdt56jx2gjmvb4awlxk3ay --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "fnxbox5ugfkr2ol5wtqbk6wkwq") | .value') >> .env.devdb
    echo KC_DB_HOST_PRIVATE=$(op item get  wos2wdt56jx2gjmvb4awlxk3ay --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "o4idffxy6bns7nihak4q4lo3xe") | .value') >> .env.devdb
    echo KC_DB_USER=keycloak >> .env.devdb
    echo KC_DB_PASS=$(op item get  wos2wdt56jx2gjmvb4awlxk3ay --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "vlf6422dpbnqhne535fpgg4vqm") | .value') >> .env.devdb
    echo KC_ADMIN_PASSWORD=$(op item get  bdmmxlepkfsqy5hfgfunpsli2i --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "password") | .value') >> .env.devdb
    echo GCP_PROJECT=$GCP_PROJECT >> .env.devdb
    echo KC_JDBC_CONNECTION= >> .env.devdb
    echo GCP_CRED=$(op item get  bdmmxlepkfsqy5hfgfunpsli2i --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "bwh5wxl5lw4yfc3lf53azij4ny") | .value') >> .env.devdb
    echo ARXIV_USER_SECRET=$(op item get  bdmmxlepkfsqy5hfgfunpsli2i --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "gxogpm2ztuyfeyvzjrwx4gqogi") | .value') >> .env.devdb
    echo LEGACY_AUTH_API_TOKEN=$(op item get  bdmmxlepkfsqy5hfgfunpsli2i --account arxiv.1password.com --format=json | jq -r '.fields[] | select(.id == "rs25xevxhbvy6l2aom7z633rti") | .value') >> .env.devdb
fi

if [ ! -r .env ] ; then
    ln -s .env.localdb .env
fi

if [ x"$KC_DB" = x"" ] ; then
    KC_DB=localdb
fi

if [ -z $1 ] ; then
  cat .env.$KC_DB
else
  gawk -F = -e "/^$1=/ {print substr(\$0,length(\" $1=\"),999)}" .env.$KC_DB
fi
