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


# Audit events

## User info update

    {
      "id" : "8b4aaf3b-14ee-4b1d-b532-79d7d178d4b8",
      "time" : 1738005796557,
      "realmId" : "c35229b5-75cf-42d4-aa83-976a0609b73d",
      "realmName" : "arxiv",
      "authDetails" : {
        "realmId" : "dc5d84a5-348f-4956-a7b9-e6a74a35cc66",
        "realmName" : "master",
        "clientId" : "1e15cfc1-4d87-465a-a369-6e70af387895",
        "userId" : "ce43077d-2b2b-4090-996f-d11757b32e83",
        "ipAddress" : "0:0:0:0:0:0:0:1"
      },
      "resourceType" : "USER",
      "operationType" : "UPDATE",
      "resourcePath" : "users/1212",
      "representation" : "{\"id\":\"1212\",\"username\":\"reader\",\"firstName\":\"Random\",\"lastName\":\"Reader\",\"email\":\"no-mail-randomreader@example.com\",\"emailVerified\":false,\"attributes\":{\"tracking_cookie\":[\"xyz\"],\"joined_date\":[\"2013-11-11T15:56:29Z\"],\"joined_ip_num\":[\"dedicated\"],\"share\":[\"FirstName\",\"LastName\",\"Email\"]},\"createdTimestamp\":1738005757855,\"enabled\":true,\"totp\":false,\"disableableCredentialTypes\":[],\"requiredActions\":[],\"notBefore\":0,\"access\":{\"manageGroupMembership\":true,\"view\":true,\"mapRoles\":true,\"impersonate\":true,\"manage\":true}}",
      "resourceTypeAsString" : "USER"
    }


## Roles assign/remove example

    {
      "id" : "3baf29ef-e42d-4531-9338-5c113d80ecaf",
      "time" : 1738104491179,
      "realmId" : "07f00f9e-e61b-4056-9b8a-e28d9c6ff245",
      "realmName" : "arxiv",
      "authDetails" : {
        "realmId" : "8b920d3c-d8ce-4da8-b27f-981ea0379004",
        "realmName" : "master",
        "clientId" : "9d541e62-065e-44be-8588-2b24b11b07f4",
        "userId" : "2d717388-1fd5-422d-8dac-0e6fb5228719",
        "ipAddress" : "0:0:0:0:0:0:0:1"
      },
      "resourceType" : "REALM_ROLE_MAPPING",
      "operationType" : "CREATE",
      "resourcePath" : "users/1212/role-mappings/realm",
      "representation" : "[{\"id\":\"f546a993-e54c-441e-861d-300d0b4624d5\",\"name\":\"Test Role\",\"description\":\"Crash dummy\",\"composite\":false,\"clientRole\":false,\"containerId\":\"07f00f9e-e61b-4056-9b8a-e28d9c6ff245\"}]",
      "resourceTypeAsString" : "REALM_ROLE_MAPPING"
    }

    {
        "id" : "1e2abec5-bf62-42b1-a000-8773cf177fab",
        "time" : 1727796557187,
        "realmId" : "e9b31419-5843-4014-9bd1-f05a2df3b96b",
        "realmName" : "arxiv",
        "authDetails" : {
            "realmId" : "e34fe449-a841-4c0c-887d-a123a565d315",
            "realmName" : "master",
            "clientId" : "350cacca-500f-41a5-a1a2-ab57a0df45b4",
            "userId" : "84e2038c-3726-463d-a131-0d09c08c0829",
            "ipAddress" : "172.17.0.1"
        },
        "resourceType" : "REALM_ROLE_MAPPING",
        "operationType" : "DELETE",
        "resourcePath" : "users/28396986-0c90-42be-b39b-73f4714debaf/role-mappings/realm",
        "representation" : "[{\"id\":\"e6350ae5-2083-46ae-bed8-ba72e3c9dfcf\",\"name\":\"Test Role\",\"composite\":false}]",
        "resourceTypeAsString" : "REALM_ROLE_MAPPING"
    }
        
