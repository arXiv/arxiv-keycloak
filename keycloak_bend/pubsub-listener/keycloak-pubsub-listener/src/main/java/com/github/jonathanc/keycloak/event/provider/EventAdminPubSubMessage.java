package com.github.jonathanc.keycloak.event.provider;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.annotation.JsonTypeInfo.Id;
import java.io.Serial;
import java.io.Serializable;
import javax.xml.bind.annotation.XmlRootElement;
import org.keycloak.events.admin.AdminEvent;

@JsonIgnoreProperties(ignoreUnknown = true)
@XmlRootElement
@JsonTypeInfo(use = Id.CLASS)
public class EventAdminPubSubMessage extends AdminEvent implements Serializable {

  @Serial private static final long serialVersionUID = -7367949289101799624L;

  public static EventAdminPubSubMessage create(final AdminEvent adminEvent) {

    final EventAdminPubSubMessage msg = new EventAdminPubSubMessage();

    msg.setAuthDetails(adminEvent.getAuthDetails());
    msg.setError(adminEvent.getError());
    msg.setOperationType(adminEvent.getOperationType());
    msg.setRealmId(adminEvent.getRealmId());
    msg.setRepresentation(adminEvent.getRepresentation());
    msg.setResourcePath(adminEvent.getResourcePath());
    msg.setResourceType(adminEvent.getResourceType());
    msg.setResourceTypeAsString(adminEvent.getResourceTypeAsString());
    msg.setTime(adminEvent.getTime());

    return msg;
  }
}
