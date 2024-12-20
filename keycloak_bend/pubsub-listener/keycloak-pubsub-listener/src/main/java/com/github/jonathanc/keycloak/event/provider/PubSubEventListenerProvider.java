package com.github.jonathanc.keycloak.event.provider;

import static java.lang.String.format;

import com.google.api.core.ApiFuture;
import com.google.api.gax.core.CredentialsProvider;
import com.google.api.gax.core.NoCredentialsProvider;
import com.google.api.gax.grpc.GrpcTransportChannel;
import com.google.api.gax.rpc.FixedTransportChannelProvider;
import com.google.api.gax.rpc.TransportChannelProvider;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.protobuf.ByteString;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.TopicName;
import io.grpc.LoadBalancerRegistry;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.internal.PickFirstLoadBalancerProvider;
import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.apache.commons.lang3.StringUtils;
import org.jboss.logging.Logger;
import org.keycloak.events.Event;
import org.keycloak.events.EventListenerProvider;
import org.keycloak.events.EventType;
import org.keycloak.events.admin.AdminEvent;
import org.keycloak.events.admin.OperationType;
import org.keycloak.util.JsonSerialization;

public class PubSubEventListenerProvider implements EventListenerProvider {

  private static final org.jboss.logging.Logger log = Logger.getLogger(
      PubSubEventListenerProvider.class);

  private final Set<EventType> excludedEvents;
  private final Set<OperationType> excludedAdminEvents;
  private final PubSubConfig cfg;

  public PubSubEventListenerProvider(
      final Set<EventType> excludedEvents,
      final Set<OperationType> excludedAdminEvents,
      final PubSubConfig cfg) {
    this.excludedAdminEvents = excludedAdminEvents;
    this.excludedEvents = excludedEvents;
    this.cfg = cfg;
    LoadBalancerRegistry.getDefaultRegistry().register(new PickFirstLoadBalancerProvider());
  }

  @Override
  public void close() {
  }

  @Override
  public void onEvent(final Event event) {
    if (this.excludedEvents == null || !this.excludedEvents.contains(event.getType())) {
      final String message = toJSON(event, true);
      this.publish(message, PubSubAttributes.createMap(event));
    }
  }

  @Override
  public void onEvent(final AdminEvent event, final boolean includeRepresentation) {
    if (this.excludedAdminEvents == null || !this.excludedAdminEvents.contains(
        event.getOperationType())) {
      final String message = toJSON(event, true);
      this.publish(message, PubSubAttributes.createMap(event));
    }
  }

  /*
   * TODO: If want to improve resource usage and velocity you can use a batchConfig.
   */
  private void publish(
      final String message, final Map<String, String> attributes) {

    Publisher publisher = null;

    try {

      final PubsubMessage pubsubMessage =
          PubsubMessage.newBuilder().setData(ByteString.copyFromUtf8(message))
              .putAllAttributes(attributes).build();
      publisher = this.getPublisher();

      final ApiFuture<String> messageIdFuture = publisher.publish(pubsubMessage);
      final String messageId = messageIdFuture.get();
      log.debug(format(
          "[PUB] published message with id '%s' and content '%s'", messageId, message));

    } catch (final Exception ex) {
      log.warn(
          format("[PUB] error publishing message with errorMessage: %s", ex.getMessage()),
          ex);
    } finally {
      if (publisher != null) {
        try {
          publisher.shutdown();
          publisher.awaitTermination(10, TimeUnit.SECONDS);
        } catch (final Exception ex) {
          log.error(
              format("[PUB] error shutting down publisher with errorMessage: %s", ex.getMessage()),
              ex);
        }
      }
    }
  }

  private Publisher getPublisher() throws IOException {

    final TopicName topicName = TopicName.of(this.cfg.getProjectId(),
        this.cfg.getAdminEventTopicId());

    final String emulatorHost = System.getenv("PUBSUB_EMULATOR_HOST");
    final boolean isEmulator = StringUtils.isNotBlank(emulatorHost);

    if (isEmulator) {
      log.warn("Starting pubsub in emulator mode.");
      final ManagedChannel channel = ManagedChannelBuilder.forTarget(emulatorHost).usePlaintext()
          .build();
      final TransportChannelProvider channelProvider =
          FixedTransportChannelProvider.create(GrpcTransportChannel.create(channel));
      final CredentialsProvider credentialsProvider = NoCredentialsProvider.create();
      return
          Publisher.newBuilder(topicName)
              .setChannelProvider(channelProvider)
              .setCredentialsProvider(credentialsProvider)
              .build();
    } else {
      return
          Publisher.newBuilder(topicName)
              .setCredentialsProvider(this.cfg.getCredentialsProvider())
              .build();
    }
  }

  public static String toJSON(final Object object, final boolean isPretty) {
    try {
      if (isPretty) {
        return JsonSerialization.writeValueAsPrettyString(object);
      }
      return JsonSerialization.writeValueAsString(object);

    } catch (final Exception ex) {
      log.error("[PUB] could not serialize keycloak Event", ex);
    }

    return "unparsable";
  }

}
