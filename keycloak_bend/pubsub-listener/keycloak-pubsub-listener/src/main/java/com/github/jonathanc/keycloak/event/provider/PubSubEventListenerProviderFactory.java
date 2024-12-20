package com.github.jonathanc.keycloak.event.provider;

import java.util.HashSet;
import java.util.Set;
import org.keycloak.Config.Scope;
import org.keycloak.events.EventListenerProvider;
import org.keycloak.events.EventListenerProviderFactory;
import org.keycloak.events.EventType;
import org.keycloak.events.admin.OperationType;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;

public class PubSubEventListenerProviderFactory implements EventListenerProviderFactory {

  private Set<EventType> excludedEvents;
  private Set<OperationType> excludedAdminOperations;
  private PubSubConfig cfg;

  @Override
  public EventListenerProvider create(final KeycloakSession session) {
    return new PubSubEventListenerProvider(this.excludedEvents, this.excludedAdminOperations,
        this.cfg);
  }

  @Override
  public void init(final Scope config) {

    // Setup configuration from cli params
    final var excludes = config.getArray("excludeEvents");
    if (excludes != null) {
      this.excludedEvents = new HashSet<>();
      for (final String e : excludes) {
        this.excludedEvents.add(EventType.valueOf(e));
      }
    }

    final String[] excludesOperations = config.getArray("excludesOperations");
    if (excludesOperations != null) {
      this.excludedAdminOperations = new HashSet<>();
      for (final String e : excludesOperations) {
        this.excludedAdminOperations.add(OperationType.valueOf(e));
      }
    }

    this.cfg = PubSubConfig.createFromScope(config);
  }

  @Override
  public void postInit(final KeycloakSessionFactory factory) {
  }

  @Override
  public void close() {
  }

  @Override
  public String getId() {
    return "kc-event-to-pubsub";
  }

}
