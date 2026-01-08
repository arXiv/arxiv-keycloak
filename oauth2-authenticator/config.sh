#!/bin/sh
. ../.env

cp ../.env ./.env

echo DOMAIN=$OAUTH2_DOMAIN >> ./.env
echo SECURE=false >> ./.env
echo PORT=21503 >> ./.env
echo KEYCLOAK_SERVER_URL=$KC_HOST_PUBLIC >> ./.env
echo OAUTH2_CALLBACK_URL=$AAA_CALLBACK_URL >> ./.env
echo ARXIV_USER_SECRET=$KEYCLOAK_TEST_CLIENT_SECRET >> ./.env
echo CLASSIC_COOKIE_NAME=tapir_session >> ./.env
echo SESSION_DURATION=$CLASSIC_SESSION_DURATION  >> ./.env
echo OIDC_SERVER_SSL_VERIFY=false  >> ./.env
echo KEYCLOAK_ADMIN_SECRET=$KC_ADMIN_PASSWORD  >> ./.env
echo AAA_API_SECRET_KEY=$AAA_API_TOKEN  >> ./.env
