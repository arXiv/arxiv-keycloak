#!/bin/bash
cd /home/keycloak
#
# spi-<spi-id>-<provider-id>-<property>=<value>
#
# https://jdbc.postgresql.org/documentation/use/
# export DEBUG=true

#
#B ootstrapping is needed only when you are starting a new cloud run
# Without this, you don't get the random? URL so you start once, and let it run even if
# it has no DB connection which the Keycloak runs with Java's memory based database as
# stand-in.
#
if [ "$BOOTSTRAP" = "yes" ] ; then
    echo "Bootstrapping"
    /opt/keycloak/bin/kc.sh start-dev
fi


if [ -z $DB_ADDR ] ; then
  echo "DB_ADDR needs to be set."
  exit 1
fi

if [ -z $KC_DB_PASS ] ; then
  echo "KC_DB_PASS needs to be set."
  exit 1
fi

if [ -z $KC_PORT ] ; then
  KC_PORT=8080
  echo "KC_PORT is default HTTP 8080"
fi

if [ -z $KC_SSL_PORT ] ; then
  echo "No HTTPS"
else
    if [ ! -r /etc/keycloak/keycloak.p12 ] ; then
        echo "/etc/keycloak/keycloak.p12 is not readable"
        exit 1
    fi
fi


if [ -r /secrets/authdb-certs/db-certs-expand.sh ] ; then
  echo "Expand db certs"
  cd /home/keycloak/certs && sh /secrets/authdb-certs/db-certs-expand.sh
  ls -l *
  cd /home/keycloak
fi

# -------------------------------------------------------------------------------------------
# Backend DB - Postgres
#
DB_VENDOR="${DB_VENDOR:-postgres}"
DB_DATABASE="${DB_DATABASE:-keycloak}"
KC_DB_USER="${KC_DB_USER:-keycloak}"

# Unfortunate that the vendor name != driver name
JDBC_DRIVER="${JDBC_DRIVER:-postgresql}"

# Database connection certificate setting for postgres db
KC_JDBC_CONNECTION="${KC_JDBC_CONNECTION:-?ssl=true&sslmode=require&sslrootcert=/home/keycloak/certs/server-ca.pem&sslcert=/home/keycloak/certs/client-cert.pem&sslkey=/home/keycloak/certs/client-key.key}"

# This shouldn't change as long as the db is postgres
DB_SCHEMA="${DB_SCHEMA:- --db-schema=public}"

# For prod, set the min larger
DB_POOL="${DB_POOL:- --db-pool-min-size=2}"

# -------------------------------------------------------------------------------------------
# proxy
#
# This is letting keycloak know that the instance is running behind a reverse proxy.
# Since the service is behind he load balancer, this should be the correct value for all cases.
# For local testing, you may want to do something different.
PROXY_MODE="${PROXY_MODE:- --proxy-headers=forwarded}"

# Since the docker is running behind the load balancer, the hostname is always inaccurate.
export KC_HOSTNAME_STRICT=false

# -------------------------------------------------------------------------------------------
# Logging
#
LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
LOG_OUTPUT_FORMAT="${LOG_OUTPUT_FORMAT:- --log-console-output=json}"

# Enable HTTP access logging - using keycloak.conf instead of JVM options
export JAVA_OPTS_APPEND="${JAVA_OPTS_APPEND} -Dquarkus.log.level=DEBUG"
export JAVA_OPTS_APPEND="${JAVA_OPTS_APPEND} -Djava.util.logging.manager=org.jboss.logmanager.LogManager"

# -------------------------------------------------------------------------------------------
# Event Listener
#

#export GCP_CREDENTIALS
#export GCP_PROJECT_ID
export GCP_EVENT_TOPIC_ID=keycloak-arxiv-events
export GCP_ADMIN_EVENT_TOPIC_ID=keycloak-arxiv-events

echo "GCP_PROJECT_ID=$GCP_PROJECT_ID"
echo "GCP_EVENT_TOPIC_ID=$GCP_EVENT_TOPIC_ID"

# HTTP buffer settings - force via JVM system properties (keycloak.conf not working)
echo "HTTP Buffer Settings: Forcing 2MB header limit via JVM properties"

# Force HTTP limits via correct JVM system properties
export JAVA_OPTS_APPEND="${JAVA_OPTS_APPEND} -Dquarkus.http.limits.max-header-size=2097152"
export JAVA_OPTS_APPEND="${JAVA_OPTS_APPEND} -Dvertx.http.maxHeaderSize=2097152" 
export JAVA_OPTS_APPEND="${JAVA_OPTS_APPEND} -Dio.vertx.core.http.HttpServerOptions.maxHeaderSize=2097152"

# -------------------------------------------------------------------------------------------
# NETWORK
#

echo "KC_PORT=$KC_PORT"
if [ ! -z $KC_SSL_PORT ] ; then
    echo "KC_SSL_PORT=$KC_SSL_PORT"
    HTTPS_ARGS="--https-port=$KC_SSL_PORT  --config-keystore=/etc/keycloak/keycloak.p12 --config-keystore-password=kcpassword --config-keystore-type=PKCS12"
else
    HTTPS_ARGS=
fi

# -------------------------------------------------------------------------------------------
# Network part 2
#
export KC_MANAGEMENT_PORT="${KC_MANAGEMENT_PORT:-9000}"
echo "KC_MANAGEMENT_PORT=$KC_MANAGEMENT_PORT"

# -------------------------------------------------------------------------------------------
# Registration
#

export ARXIV_USER_REGISTRATION_URL

# -------------------------------------------------------------------------------------------
# start / start-dev
#
KEYCLOAK_START="${KEYCLOAK_START:-start-dev}"

#  --http-port ${KC_PORT} --https-port ${KC_SSL_PORT} --config-keystore=/path/to/keystore.p12 --config-keystore-password=keystorepass --config-keystore-type=PKCS12

export KC_DB_URL="jdbc:$JDBC_DRIVER://$DB_ADDR/$DB_DATABASE$KC_JDBC_CONNECTION"
echo KC_DB_URL=$KC_DB_URL

# Start Keycloak using keycloak.conf for HTTP settings
/opt/keycloak/bin/kc.sh $KEYCLOAK_START \
  --log-level=$LOG_LEVEL \
  --http-port=$KC_PORT \
  --verbose \
  --transaction-xa-enabled=true \
  --db=$DB_VENDOR \
  --db-url=$KC_DB_URL \
  --db-username=$KC_DB_USER \
  --db-password=$KC_DB_PASS \
  $HTTPS_ARGS \
  --http-management-port=$KC_MANAGEMENT_PORT \
  $HTTP_OPTS \
  $DB_SCHEMA $PROXY_MODE $LOG_OUTPUT_FORMAT
