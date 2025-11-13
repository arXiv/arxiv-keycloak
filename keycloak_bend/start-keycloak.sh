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


# Handle SSL certificates - supports three methods:
# Method 1: Individual certificate files (new, recommended)
#   - Certificates mounted at separate /secrets/ locations
#   - /secrets/authdb-server-ca/server-ca.pem
#   - /secrets/authdb-client-cert/client-cert.pem
#   - /secrets/authdb-client-key-pem/client-key.pem
#   - /secrets/authdb-client-key-der/client-key.key.b64
#   - Copied to /home/keycloak/certs/ at startup
# Method 2: Shell script bundle (legacy, backward compatibility)
#   - Single secret containing shell script at /secrets/authdb-certs/db-certs-expand.sh
#   - Script creates certificate files in /home/keycloak/certs/
# Method 3: Old individual mounts (legacy)
#   - Certificates at /secrets/authdb-certs/*.pem

echo "=== SSL Certificate Setup ==="

# Method 1: Check if certificates are mounted in separate secret locations (new approach)
if [ -r /secrets/authdb-server-ca/server-ca.pem ] && [ -r /secrets/authdb-client-cert/client-cert.pem ] && [ -r /secrets/authdb-client-key-pem/client-key.pem ]; then
  echo "Method 1: Found individually mounted SSL certificates in /secrets/"
  echo "Copying certificates to /home/keycloak/certs/..."

  # Create target directory
  mkdir -p /home/keycloak/certs

  # Copy certificates from separate mount locations
  # Use cat redirection instead of cp to avoid symlink issues with Cloud Run secret mounts
  cat /secrets/authdb-server-ca/server-ca.pem > /home/keycloak/certs/server-ca.pem
  cat /secrets/authdb-client-cert/client-cert.pem > /home/keycloak/certs/client-cert.pem
  cat /secrets/authdb-client-key-pem/client-key.pem > /home/keycloak/certs/client-key.pem

  # Set permissions
  chmod 644 /home/keycloak/certs/server-ca.pem
  chmod 644 /home/keycloak/certs/client-cert.pem
  chmod 600 /home/keycloak/certs/client-key.pem

  echo ""
  echo "Certificate file checks:"
  echo "  ✓ server-ca.pem copied"
  echo "  ✓ client-cert.pem copied"
  echo "  ✓ client-key.pem copied"

  # Decode binary DER key if base64-encoded version is present
  if [ -r /secrets/authdb-client-key-der/client-key.key.b64 ]; then
    echo "  ✓ client-key.key.b64 found, decoding to binary DER format..."
    if base64 -d /secrets/authdb-client-key-der/client-key.key.b64 > /home/keycloak/certs/client-key.key; then
      chmod 600 /home/keycloak/certs/client-key.key
      echo "  ✓ client-key.key decoded successfully"
    else
      echo "  ✗ ERROR: Failed to decode client-key.key.b64"
    fi
  fi

  echo ""
  echo "Final certificate directory contents:"
  ls -la /home/keycloak/certs/
  echo ""

# Method 2: Try shell script bundle (legacy approach for backward compatibility)
elif [ -r /secrets/authdb-certs/db-certs-expand.sh ]; then
  echo "Method 2: Found legacy shell script bundle at /secrets/authdb-certs/db-certs-expand.sh"
  echo "Expanding certificates from script..."
  mkdir -p /home/keycloak/certs
  cd /home/keycloak/certs

  echo "Running: sh /secrets/authdb-certs/db-certs-expand.sh"
  if sh /secrets/authdb-certs/db-certs-expand.sh; then
    echo "  ✓ Successfully executed db-certs-expand.sh"
    echo "Certificate files created:"
    ls -la /home/keycloak/certs/
  else
    echo "  ✗ ERROR: Failed to execute db-certs-expand.sh (exit code: $?)"
  fi
  cd /home/keycloak
  echo ""

# Method 3: Fallback to individually mounted files in old location
elif [ -r /secrets/authdb-certs/server-ca.pem ]; then
  echo "Method 3: Found individually mounted certificates in /secrets/authdb-certs/"
  echo "Copying certificate files to /home/keycloak/certs/..."
  mkdir -p /home/keycloak/certs
  cp -v /secrets/authdb-certs/server-ca.pem /home/keycloak/certs/
  cp -v /secrets/authdb-certs/client-cert.pem /home/keycloak/certs/
  cp -v /secrets/authdb-certs/client-key.pem /home/keycloak/certs/
  if [ -f /secrets/authdb-certs/client-key.key ]; then
    cp -v /secrets/authdb-certs/client-key.key /home/keycloak/certs/
  fi
  chmod 644 /home/keycloak/certs/*.pem 2>/dev/null || true
  chmod 600 /home/keycloak/certs/*.key 2>/dev/null || true
  echo "Certificate files copied:"
  ls -la /home/keycloak/certs/
  echo ""

else
  echo "WARNING: No SSL certificates found!"
  echo "Database connection may fail if SSL is required."
  echo "Checked locations:"
  echo "  - /secrets/authdb-server-ca/ (new individual mounts)"
  echo "  - /secrets/authdb-certs/db-certs-expand.sh (legacy shell script)"
  echo "  - /secrets/authdb-certs/*.pem (legacy individual files)"
fi

# Final verification
if [ -d /home/keycloak/certs ]; then
  echo "Final certificate directory contents:"
  ls -la /home/keycloak/certs/
  echo ""
  echo "Final certificate checks:"
  [ -r /home/keycloak/certs/server-ca.pem ] && echo "  ✓ server-ca.pem is readable" || echo "  ✗ server-ca.pem NOT readable"
  [ -r /home/keycloak/certs/client-cert.pem ] && echo "  ✓ client-cert.pem is readable" || echo "  ✗ client-cert.pem NOT readable"
  [ -r /home/keycloak/certs/client-key.key ] && echo "  ✓ client-key.key is readable" || echo "  ✗ client-key.key NOT readable"
else
  echo "WARNING: /home/keycloak/certs directory does not exist!"
fi
echo "=== End SSL Certificate Setup ==="
echo ""

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

GCP_EVENT_TOPIC_ID="${GCP_EVENT_TOPIC_ID:-keycloak-arxiv-events}"
GCP_ADMIN_EVENT_TOPIC_ID="${GCP_ADMIN_EVENT_TOPIC_ID:-keycloak-arxiv-events}"
export GCP_EVENT_TOPIC_ID=keycloak-arxiv-events
export GCP_ADMIN_EVENT_TOPIC_ID=keycloak-arxiv-events

echo "GCP_PROJECT_ID=$GCP_PROJECT_ID"
echo "GCP_EVENT_TOPIC_ID=$GCP_EVENT_TOPIC_ID"
echo "GCP_ADMIN_EVENT_TOPIC_ID=$GCP_ADMIN_EVENT_TOPIC_ID"

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
echo "KC_DB_URL=$KC_DB_URL"

echo ""
echo "=== Environment and Resource Diagnostics ==="
echo "Current user: $(id)"
echo "Working directory: $(pwd)"
echo "Memory info:"
free -h || echo "free command not available"
echo ""
echo "Disk space:"
df -h /home/keycloak || echo "df command failed"
echo ""
echo "Key environment variables:"
echo "  DB_VENDOR=$DB_VENDOR"
echo "  DB_ADDR=$DB_ADDR"
echo "  DB_DATABASE=$DB_DATABASE"
echo "  KC_DB_USER=$KC_DB_USER"
echo "  KC_DB_PASS=[REDACTED - length: ${#KC_DB_PASS}]"
echo "  KEYCLOAK_START=$KEYCLOAK_START"
echo "  LOG_LEVEL=$LOG_LEVEL"
echo "  GCP_PROJECT_ID=$GCP_PROJECT_ID"
echo "  GCP_EVENT_TOPIC_ID=$GCP_EVENT_TOPIC_ID"
echo "  ARXIV_USER_REGISTRATION_URL=$ARXIV_USER_REGISTRATION_URL"
echo "  JAVA_OPTS_APPEND=$JAVA_OPTS_APPEND"
echo ""
echo "Checking database connectivity:"
echo "  Attempting to resolve DB_ADDR: $DB_ADDR"
if command -v getent >/dev/null 2>&1; then
  getent hosts "$DB_ADDR" || echo "  WARNING: Could not resolve $DB_ADDR"
else
  echo "  getent not available, skipping DNS check"
fi
echo "=== End Environment and Resource Diagnostics ==="
echo ""

echo "=== Cloud SQL Proxy Diagnostics ==="
echo "Checking if port 5432 (Cloud SQL Proxy) is listening..."
# Port 5432 in hex is 1538, check /proc/net/tcp
if grep -q ":1538 " /proc/net/tcp 2>/dev/null; then
  echo "  ✓ Port 5432 is listening"
else
  echo "  ✗ WARNING: Port 5432 is NOT listening"
  echo "  Tip: Cloud SQL Proxy might not be injected or failed to start"
fi
echo "=== End Cloud SQL Proxy Diagnostics ==="
echo ""

echo "=== Starting Keycloak ==="
echo "Command: /opt/keycloak/bin/kc.sh $KEYCLOAK_START"
echo "Arguments:"
echo "  --log-level=$LOG_LEVEL"
echo "  --http-port=$KC_PORT"
echo "  --verbose"
echo "  --transaction-xa-enabled=true"
echo "  --db=$DB_VENDOR"
echo "  --db-url=$KC_DB_URL"
echo "  --db-username=$KC_DB_USER"
echo "  --db-password=[REDACTED]"
echo "  --http-management-port=$KC_MANAGEMENT_PORT"
echo "  $DB_SCHEMA $PROXY_MODE $LOG_OUTPUT_FORMAT"
[ -n "$HTTPS_ARGS" ] && echo "  HTTPS: $HTTPS_ARGS"
echo ""
echo "Keycloak is starting... (this may take several minutes)"
echo "Timestamp: $(date -Iseconds)"
echo ""

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

KC_EXIT_CODE=$?
echo ""
echo "=== Keycloak Process Exited ==="
echo "Exit code: $KC_EXIT_CODE"
echo "Timestamp: $(date -Iseconds)"
if [ $KC_EXIT_CODE -ne 0 ]; then
  echo "ERROR: Keycloak exited with non-zero status: $KC_EXIT_CODE"
  echo "Common causes:"
  echo "  - Database connection failure"
  echo "  - Out of memory (check Cloud Run memory limits)"
  echo "  - Configuration error"
  echo "  - Port already in use"
  exit $KC_EXIT_CODE
else
  echo "Keycloak exited normally"
fi
