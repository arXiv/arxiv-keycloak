
keycloak-pubsub-listener/target/keycloak-to-pubsub-jar-with-dependencies.jar: keycloak-pubsub-listener /usr/bin/java /usr/bin/mvn
	cd keycloak-pubsub-listener && mvn clean install

keycloak-pubsub-listener: 
	git clone https://github.com/Jojoooo1/keycloak-pubsub-listener.git

/usr/bin/java:
	sudo apt install -y openjdk-21-jdk

/usr/bin/mvn: /usr/bin/java
	sudo apt install -y maven
