# keycloak-event-listener-gcpubsub

##### A Keycloak SPI plugin that publishes events to Google Cloud Pub/Sub.

For example here is the notification of the user updated by administrator

* attributes:

```
eventType: "ADMIN"
realmId: "MYREALM"
resourceType: "USER"
operationType: "UPDATE"
```

* content:

```
{
  "@class" : "com.github.jonathanc.keycloak.event.provider.EventAdminPubSubMessage",
  "time" : 1596951200408,
  "realmId" : "MYREALM",
  "authDetails" : {
    "realmId" : "master",
    "clientId" : "********-****-****-****-**********",
    "userId" : "********-****-****-****-**********",
    "ipAddress" : "192.168.1.1"
  },
  "resourceType" : "USER",
  "operationType" : "UPDATE",
  "resourcePath" : "users/********-****-****-****-**********",
  "representation" : "representation details here....",
  "error" : null,
  "resourceTypeAsString" : "USER"
}
```

## USAGE:

1. build from source: `make package`
2. copy jar into your Keycloak `/opt/keycloak/providers/keycloak-to-pubsub-1.0.jar`
3. Restart the Keycloak server
4. Enable pubsub in Keycloak UI by adding **pubsub**  
   `Manage > Events > Config > Events Config > Event Listeners`

#### Configuration

###### configure **ENVIRONMENT VARIABLES**

- `GCP_CREDENTIALS` -> your GCP service-account.json in base64
- `GCP_PROJECT_ID`
- `GCP_TOPIC_ID`
- `GCP_ADMIN_TOPIC_ID`

#### Testing

If you want to use pubsub emulator uncomment `PUBSUB_EMULATOR_HOST=pubsub:8085`
in `docker-compose.yaml`

#### TODO

Add cli params to only publish admin event in order to improve resource usage. This is the most
common use case to sync keycloak user and external database.


