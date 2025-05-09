package org.arxiv.keycloak.validator;

import org.keycloak.Config;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.validate.Validator;
import org.keycloak.validate.ValidatorFactory;

import java.util.Collections;
import java.util.List;

public class ArxivUsernameValidatorFactory implements ValidatorFactory {

    private final ArxivUsernameValidator validator = new ArxivUsernameValidator();

    @Override
    public Validator create(KeycloakSession session) {
        // Required by ProviderFactory<Validator>
        return validator;
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
        // No-op
    }

    @Override
    public void init(Config.Scope config) {
        // No-op
    }

    @Override
    public void close() {
        // No-op
    }

    @Override
    public String getId() {
        return "arxiv-username-validator-factory";
    }

    @Override
    public List<ProviderConfigProperty> getConfigMetadata() {
        return Collections.emptyList();
    }
}
