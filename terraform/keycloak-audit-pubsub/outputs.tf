output "topic_name" {
  value = basename(google_pubsub_topic.keycloak-arxiv-events.name)
}

output "topic_id" {
  value = basename(google_pubsub_topic.keycloak-arxiv-events.id)
}
