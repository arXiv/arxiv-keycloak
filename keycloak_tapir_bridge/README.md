# Keycloak -> Tapir bridge

The service subscribes to the queue and updates the database accordingly to the evens
coming out from Keycloak.

## Running under debugger

Once docker compose up is up and running, you need to kill the keycloak-tapir-bridge to
open up the port.

    docker kill keycloak-tapir-bridge

ENTRYPOINT:

    src/main.py

ARGS:

    --project arxiv-development --subscription=keycloak-arxiv-events-sub --debug

ENVS:

    CLASSIC_DB_URI=mysql+mysqldb://arxiv:arxiv_password@127.0.0.1:21504/arXiv?ssl=false&ssl_mode=DISABLED
    PUBSUB_EMULATOR_HOST=127.0.0.1:21507
    PUBSUB_TOPIC=keycloak-arxiv-events
    SUBSCRIPTION=keycloak-arxiv-events-sub

