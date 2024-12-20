#!/bin/bash

if [ ! -r .env.localdb ] ; then
    echo KC_DOCKER_TAG=gcr.io/arxiv-development/keycloak >> .env.localdb
    echo DB_ADDR_PUBLIC=127.0.0.1 >> .env.localdb
    echo DB_ADDR_PRIVATE=invalid >> .env.localdb
    echo DB_USER=keycloak >> .env.localdb
    echo DB_PASS=$(op item get wos2wdt56jx2gjmvb4awlxk3ay --format=json | jq -r '.fields[] | select(.id == "vlf6422dpbnqhne535fpgg4vqm") | .value') >> .env.localdb
    echo KC_ADMIN_PASSWORD=$(op item get bdmmxlepkfsqy5hfgfunpsli2i --format=json | jq -r '.fields[] | select(.id == "password") | .value') >> .env.localdb
    echo GCP_PROJECT=arxiv-development >> .env.localdb
    echo JDBC_CONNECTION="?ssl=false&sslmode=disable" >> .env.localdb
    echo GCP_CRED= >> .env.localdb
    echo ARXIV_USER_SECRET=$(op item get bdmmxlepkfsqy5hfgfunpsli2i --format=json | jq -r '.fields[] | select(.id == "gxogpm2ztuyfeyvzjrwx4gqogi") | .value') >> .env.localdb
fi

if [ ! -r .env.devdb ] ; then
    echo KC_DOCKER_TAG=gcr.io/arxiv-development/keycloak >> .env.devdb
    echo DB_ADDR_PUBLIC=$(op item get wos2wdt56jx2gjmvb4awlxk3ay --format=json | jq -r '.fields[] | select(.id == "fnxbox5ugfkr2ol5wtqbk6wkwq") | .value') >> .env.devdb
    echo DB_ADDR_PRIVATE=$(op item get wos2wdt56jx2gjmvb4awlxk3ay --format=json | jq -r '.fields[] | select(.id == "o4idffxy6bns7nihak4q4lo3xe") | .value') >> .env.devdb
    echo DB_USER=keycloak >> .env.devdb
    echo DB_PASS=$(op item get wos2wdt56jx2gjmvb4awlxk3ay --format=json | jq -r '.fields[] | select(.id == "vlf6422dpbnqhne535fpgg4vqm") | .value') >> .env.devdb
    echo KC_ADMIN_PASSWORD=$(op item get bdmmxlepkfsqy5hfgfunpsli2i --format=json | jq -r '.fields[] | select(.id == "password") | .value') >> .env.devdb
    echo GCP_PROJECT=arxiv-development >> .env.devdb
    echo JDBC_CONNECTION= >> .env.devdb
    echo GCP_CRED=$(op item get bdmmxlepkfsqy5hfgfunpsli2i --format=json | jq -r '.fields[] | select(.id == "bwh5wxl5lw4yfc3lf53azij4ny") | .value') >> .env.devdb
    echo ARXIV_USER_SECRET=$(op item get bdmmxlepkfsqy5hfgfunpsli2i --format=json | jq -r '.fields[] | select(.id == "gxogpm2ztuyfeyvzjrwx4gqogi") | .value') >> .env.envdb
fi

if [ ! -r .env ] ; then
    cp .env.localdb .env
fi

if [ x"$KC_DB" = x"" ] ; then
    KC_DB=localdb
fi

if [ -z $1 ] ; then
  cat .env.$KC_DB
else
  gawk -F = -e "/^$1=/ {print substr(\$0,length(\" $1=\"),999)}" .env.$KC_DB
fi
