FROM quay.io/keycloak/keycloak:26.1.2

# ARG CERT_DIR

USER root

# SSL certificates to connect to database
# In local dev, you'd need this to talk to the database on GCP.
# In prod, this is likely done as proxy
RUN mkdir -p /home/keycloak/certs

# Java Spring config file
COPY keycloak.conf /opt/keycloak/conf/keycloak.conf
RUN chown keycloak /opt/keycloak/conf/keycloak.conf

# Start up script
COPY start-keycloak.sh /home/keycloak/start-keycloak.sh
RUN chmod 755 /home/keycloak/start-keycloak.sh /home/keycloak/certs

# REST api call for user migration
COPY ./keycloak_migration/keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar /opt/keycloak/providers/

# Pub/sub event posting
COPY ./pubsub-listener/keycloak-to-pubsub-jar-with-dependencies.jar /opt/keycloak/providers/

# Themes
COPY ./kcfy-arxiv/dist_keycloak/keycloak-theme-for-kc-all-other-versions.jar /opt/keycloak/providers/kc-arXiv-react-theme.jar

# Username with "#" validator SPI
# No longer needed. You can use regex
# COPY ./arxiv-username-validator/target/arxiv-username-validator-1.0.0.jar /opt/keycloak/providers/arxiv-username-validator-1.0.0.jar

RUN chown -R keycloak /home/keycloak /opt/keycloak/providers /opt/keycloak/themes/

USER keycloak
WORKDIR /home/keycloak

RUN /opt/keycloak/bin/kc.sh build
ENTRYPOINT ["/home/keycloak/start-keycloak.sh"]
