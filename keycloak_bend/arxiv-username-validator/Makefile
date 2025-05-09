.PHONY: clean
default: target/arxiv-username-validator-1.0.0.jar

target/arxiv-username-validator-1.0.0.jar: src/main/java/org/arxiv/keycloak/validator/ArxivUsernameValidatorFactory.java src/main/java/org/arxiv/keycloak/validator/ArxivUsernameValidator.java src/main/resources/META-INF/services/org.keycloak.validate.ValidatorFactory
	mvn clean package

clean:
	rm -fr target
