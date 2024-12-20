#!/bin/bash
set -x
# Variables
DB_NAME="keycloak"
DB_USER="keycloak"
DB_PASSWORD=$(../config.sh DB_PASS)
POSTGRES_VERSION="16"
POSTGRES_CONFIG_PATH=$(find /etc/postgresql -name postgresql.conf | grep "$POSTGRES_VERSION")
KEYCLOAK_HOME="/opt/keycloak"  # Change this to your Keycloak installation directory
# 
JDBC_DRIVER_URL="https://jdbc.postgresql.org/download/postgresql-42.2.29.jar"
NETWORK="0.0.0.0"  # Adjust this if you need remote access


# Function to install PostgreSQL
install_postgresql() {
    echo "Updating package list and installing PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
}

# Function to create PostgreSQL database and user
create_keycloak_db() {
    echo "Configuring PostgreSQL for Keycloak..."

    sudo -i -u postgres psql <<EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF
}

# 
setup_keycloak_user() {
    echo " Keycloak user..."
    sudo -i -u postgres psql ${DB_NAME} <<EOF
GRANT USAGE ON SCHEMA PUBLIC TO ${DB_USER};
GRANT CREATE ON SCHEMA PUBLIC TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA PUBLIC GRANT ALL ON TABLES TO ${DB_USER};
EOF

}


# Function to configure PostgreSQL for external access
configure_postgres_access() {
    echo "Enabling remote access for PostgreSQL..."
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" ${POSTGRES_CONFIG_PATH}
    echo "host    ${DB_NAME}    ${DB_USER}    ${NETWORK}   md5" | sudo tee -a /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf
    echo "host    ${DB_NAME}    ${DB_USER}    172.17.0.0/16           md5" | sudo tee -a /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf

    sudo systemctl restart postgresql
}

# Function to configure Keycloak database settings

configure_keycloak() {
    echo "Configuring Keycloak to use PostgreSQL..."
    sudo mkdir -p $KEYCLOAK_HOME/conf
    sudo chown -R $USER $KEYCLOAK_HOME
    cat <<EOF > $KEYCLOAK_HOME/conf/keycloak.conf
db=postgres
db-url=jdbc:postgresql://localhost:5432/${DB_NAME}
db-username=${DB_USER}
db-password=$DB_PASSWORD
EOF

    echo "Downloading PostgreSQL JDBC driver..."
    wget $JDBC_DRIVER_URL -P $KEYCLOAK_HOME/providers
}

# Function to test PostgreSQL connection
test_postgres_connection() {
    echo "Testing PostgreSQL connection for $DB_USER on $DB_NAME..."
    PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "\dt" || {
        echo "Connection test failed. Check your configuration."
        exit 1
    }
    echo "Connection test successful."
}

# Execute functions

install_postgresql
create_keycloak_db
setup_keycloak_user
configure_postgres_access
configure_keycloak
test_postgres_connection

echo "PostgreSQL setup for Keycloak completed successfully."
