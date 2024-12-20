
SUBDIRS = keycloak_bend oauth2-authenticator keycloak_tapir_bridge 

all: bootstrap

bootstap: $(SUBDIRS:%=%-setup)

%-bootstrap:
	$(MAKE) -C $* bootstrap

