package com.github.jonathanc.keycloak.event.provider;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.annotation.JsonTypeInfo.Id;
import java.io.Serial;
import java.io.Serializable;
import javax.xml.bind.annotation.XmlRootElement;
import org.keycloak.events.Event;

@JsonIgnoreProperties(ignoreUnknown = true)
@XmlRootElement
@JsonTypeInfo(use = Id.CLASS)
public class EventClientPubSubMessage extends Event implements Serializable {

  @Serial private static final long serialVersionUID = -2192461924304841222L;

  public static EventClientPubSubMessage create(final Event event) {

    final EventClientPubSubMessage msg = new EventClientPubSubMessage();

    msg.setClientId(event.getClientId());
    msg.setDetails(event.getDetails());
    msg.setError(event.getError());
    msg.setIpAddress(event.getIpAddress());
    msg.setRealmId(event.getRealmId());
    msg.setSessionId(event.getSessionId());
    msg.setTime(event.getTime());
    msg.setType(event.getType());
    msg.setUserId(event.getUserId());

    return msg;
  }
}
