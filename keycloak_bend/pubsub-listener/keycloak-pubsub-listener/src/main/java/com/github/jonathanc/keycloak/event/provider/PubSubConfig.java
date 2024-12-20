package com.github.jonathanc.keycloak.event.provider;

import static java.lang.String.format;

import com.google.api.gax.core.CredentialsProvider;
import com.google.api.gax.core.FixedCredentialsProvider;
import com.google.auth.oauth2.ServiceAccountCredentials;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.Base64;
import org.jboss.logging.Logger;
import org.keycloak.Config.Scope;

public class PubSubConfig {

  private static final Logger log = Logger.getLogger(PubSubConfig.class.getName());

  private String projectId;
  private String eventTopicId;
  private String adminEventTopicId;
  private String gcpCredentialsEncodedKey;

  public static PubSubConfig createFromScope(final Scope config) {
    final PubSubConfig cfg = new PubSubConfig();

    cfg.setProjectId(resolveConfigVar(config, "project_id"));
    cfg.setEventTopicId(resolveConfigVar(config, "event_topic_id"));
    cfg.setAdminEventTopicId(resolveConfigVar(config, "admin_event_topic_id"));
    cfg.setGcpCredentialsEncodedKey(resolveConfigVar(config, "credentials"));

    return cfg;
  }

  public CredentialsProvider getCredentialsProvider() throws IOException {
    return FixedCredentialsProvider.create(
        ServiceAccountCredentials.fromStream(
            new ByteArrayInputStream(Base64.getDecoder().decode(this.gcpCredentialsEncodedKey))));
  }

  public String getProjectId() {
    return this.projectId;
  }

  public void setProjectId(final String projectId) {
    this.projectId = projectId;
  }

  public void setEventTopicId(final String eventTopicId) {
    this.eventTopicId = eventTopicId;
  }

  public void setAdminEventTopicId(final String adminEventTopicId) {
    this.adminEventTopicId = adminEventTopicId;
  }

  public void setGcpCredentialsEncodedKey(final String gcpCredentialsEncodedKey) {
    this.gcpCredentialsEncodedKey = gcpCredentialsEncodedKey;
  }

  public String getEventTopicId() {
    return this.eventTopicId;
  }

  public String getAdminEventTopicId() {
    return this.adminEventTopicId;
  }

  public String getGcpCredentialsEncodedKey() {
    return this.gcpCredentialsEncodedKey;
  }

  private static String resolveConfigVar(final Scope config, final String variableName) {

    String value = null;
    if (config != null && config.get(variableName) != null) {
      value = config.get(variableName);
    } else {
      final String envVariableName = "GCP_" + variableName.toUpperCase();
      if (System.getenv(envVariableName) != null) {
        value = System.getenv(envVariableName);
      }
    }

    if (value == null) {
      final String msg = format("[PLUGIN] configuration: GCP_%s not set up.",
          variableName.toUpperCase());
      log.error(msg);
      throw new RuntimeException(msg);
    }
    return value;
  }

}
