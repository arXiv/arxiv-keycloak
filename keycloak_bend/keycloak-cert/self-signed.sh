#!/bin/sh
openssl req -new -x509 -days 365 -nodes -keyout keycloak-self-signed.key -out keycloak-self-signed.crt -config localhost.cnf
openssl pkcs12 -export -in keycloak-self-signed.crt -inkey keycloak-self-signed.key -out keycloak-self-signed.p12 -name keycloak-self-signed -passout pass:kcpassword
echo kcpassword | keytool -importkeystore -srckeystore keycloak-self-signed.p12 -srcstoretype PKCS12 -destkeystore keycloak-self-signed.jks -deststoretype JKS -deststorepass kcpassword
