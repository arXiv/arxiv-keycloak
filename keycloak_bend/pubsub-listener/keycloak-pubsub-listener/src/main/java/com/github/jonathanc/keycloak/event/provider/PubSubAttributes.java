package com.github.jonathanc.keycloak.event.provider;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.annotation.JsonTypeInfo.Id;
import java.io.Serial;
import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import javax.xml.bind.annotation.XmlRootElement;
import org.keycloak.events.Event;
import org.keycloak.events.admin.AdminEvent;

@JsonIgnoreProperties(ignoreUnknown = true)
@XmlRootElement
@JsonTypeInfo(use = Id.CLASS)
public class PubSubAttributes implements Serializable {

  @Serial private static final long serialVersionUID = 2818331369850992957L;

  public static Map<String, String> createMap(final AdminEvent adminEvent) {
    final Map<String, String> map = new HashMap<>();
    map.put("eventType", "ADMIN");
    map.put("realmId", adminEvent.getRealmId());
    map.put("errorStatus", (adminEvent.getError() != null ? "ERROR" : "SUCCESS"));
    map.put("resourceType", adminEvent.getResourceTypeAsString());
    map.put("operationType", adminEvent.getOperationType().toString());
    return map;
  }

  public static Map<String, String> createMap(final Event event) {
    final Map<String, String> map = new HashMap<>();
    map.put("eventType", "CLIENT");
    map.put("realmId", event.getRealmId());
    map.put("errorStatus", (event.getError() != null ? "ERROR" : "SUCCESS"));
    map.put("eventId", event.getType().toString());
    if (event.getClientId() != null) {
      map.put("clientId", event.getClientId());
    }
    return map;
  }
}
