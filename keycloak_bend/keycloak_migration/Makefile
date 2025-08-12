
all: keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar 


keycloak-user-migration:
	git clone https://github.com/daniel-frak/keycloak-user-migration.git

keycloak-user-migration/target/keycloak-rest-provider-5.0.1-SNAPSHOT.jar: keycloak-user-migration setup-$(OS)
	cd keycloak-user-migration && mvn clean install

setup-debian: /usr/bin/java /usr/bin/mvn

#setup-arch:

/usr/bin/java:
	sudo apt install -y openjdk-21-jdk

/usr/bin/mvn: /usr/bin/java
	sudo apt install -y maven
