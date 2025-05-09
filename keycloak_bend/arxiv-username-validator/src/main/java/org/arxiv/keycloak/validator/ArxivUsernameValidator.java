package org.arxiv.keycloak.validator;

import org.keycloak.validate.Validator;
import org.keycloak.validate.ValidationContext;
import org.keycloak.validate.ValidationError;
import org.keycloak.validate.ValidatorConfig;

import java.util.regex.Pattern;

public class ArxivUsernameValidator implements Validator {

    public static final String ID = "arxiv-username-validator";

    private static final Pattern PATTERN = Pattern.compile("^[a-zA-Z0-9._#-]{1,255}$");

    @Override
    public ValidationContext validate(Object value, String inputHint, ValidationContext context, ValidatorConfig config) {
        String username = value == null ? null : value.toString();
        if (username == null || !PATTERN.matcher(username).matches()) {
            context.addError(new ValidationError(ID, inputHint, "Invalid username format"));
        }
        return context;
    }
}
