
ENVIRONMENTS := development production stage
TOPIC_NAME = keycloak-audit-event
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile


#-#
#-# Command: kc-audit-topic
#-#   creates/updates the keycloak audit event pubsub topic
#-#   in all available environments.
#-#   Can be combined with the environment like
#-#     make kc-audit-topic-development
kc-audit-topic: $(addprefix kc-audit-topic-,${ENVIRONMENTS})

kc-audit-topic-%:
	if gcloud pubsub topics list --project arxiv-$* \
		| grep -qE  "^name: projects/arxiv-$*/topics/${TOPIC_NAME}" ; then \
			COMMAND=update ; else COMMAND=create ; fi ; \
	gcloud pubsub topics $${COMMAND} \
		--project arxiv-$* \
		--message-retention-duration=1d \
		${TOPIC_NAME}

